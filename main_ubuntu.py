import os, subprocess, argparse, glob, time, shutil, pickle, sys
from Config_handler import Config_handler
from Utils import *
from MLA.extract_numerical_features import *
from MLA.Learn import predictKFoldSVM, predictAndTestKFoldSVM, predictKFoldSVMSSK, calculateMetrics, \
    get_indices_of_misclassified_apps, predictKFoldTrees, predictKFoldKNN, predictKFoldSVM
from shutil import copyfile


# location to set the number of cores /usr/local/lib/python3.6/site-packages/acfg_tools/builder/app_graph.py

# Run command
# python3 main.py -explorer_dir "/Users/jonaneumeier/Dropbox/Uni/6. Semester/Bachelor-thesis/bachelor_code/grodd_new_version/BranchExplorer" -inputDir /Users/jonaneumeier/Dropbox/Uni/6.\ Semester/Bachelor-thesis/bachelor_code/test_data/input -outputDir /Users/jonaneumeier/Dropbox/Uni/6.\ Semester/Bachelor-thesis/bachelor_code/test_data/output

# Run command Ubuntu machine
# python3 main.py -explorer_dir "/home/aesalem/Jona/phenax/grodd_new_version/BranchExplorer" -inputDir "/home/aesalem/Jona/phenax/IO/input" -outputDir "/home/aesalem/Jona/phenax/IO/output"

# prettyPrint color options: info, error, warning, info2, output, debug

def setup_Arguments():
    parser = argparse.ArgumentParser(prog="main.py",
                                     description="This is the main program. TODO: explain the program here briefly")
    parser.add_argument("-explorer_dir", "--branchExplorer_dir",
                        help="The path to the subdirectory BranchExplorer in the GroddDroid files", required=True)
    parser.add_argument("-inputDir", "--inputDirectory",
                        help="The path to the directory with the input APKs. It should contain two directories train and test, each of them should ahve two folder malware and goodware as well",
                        required=True)
    parser.add_argument("-outputDir", "--outputDirectory", help="The path to the directory for the output",
                        required=True)
    parser.add_argument("-kf", "--kfold", help="Set the value of K for cross validation", default=2)
    parser.add_argument("-selectBest", "--selectBest",
                        help="Set the number of the features that should be selected >= 30", default=0)
    parser.add_argument("-VMname", "--vm_name", help="The name or ID of the Virtual Box virtual machine to use",
                        default="7e44e530-9603-44af-9c03-72d5654130e7")
    parser.add_argument("-restore_snapshot", "--restore_snapshot",
                        help="The name or ID of the Virtual Box snapshot to restore the virtual machine",
                        default="117f78c8-97da-4acc-a6a8-d12e4d14d85e")
    return parser


genyProcess = None


def main():
    """Main method which handles the overall process"""

    argumentParser = setup_Arguments()
    arguments = argumentParser.parse_args()

    ###############################################################################################################
    # Retrive the apk files form the input directory and prepare output directory
    ###############################################################################################################
    if os.path.exists(arguments.outputDirectory + "/results.txt"):
        os.remove(arguments.outputDirectory + "/results.txt")
    if os.path.exists(arguments.outputDirectory + "/ml_input.txt"):
        os.remove(arguments.outputDirectory + "/ml_input.txt")
    if os.path.exists(arguments.outputDirectory + "/X_database.txt"):
        os.remove(arguments.outputDirectory + "/X_database.txt")
    if os.path.exists(arguments.outputDirectory + "/y_database.txt"):
        os.remove(arguments.outputDirectory + "/y_database.txt")
    for file in glob.glob(arguments.outputDirectory + "/*"):
        shutil.rmtree(file)

    if not os.path.exists(arguments.inputDirectory):
        prettyPrint("Unable to open the input directory", "error")
        return False

    if not os.path.exists(arguments.outputDirectory):
        os.makedirs(arguments.outputDirectory)

    f = open(arguments.outputDirectory + "/results.txt", "a")
    f.write("############################################################################\n")
    f.write("# Start time: %s #\n" % (getTimestamp()))
    f.write("############################################################################\n")
    f.close()

    f = open(arguments.outputDirectory + "/ml_input.txt", "a")
    f.write("############################################################################\n")
    f.write(
        "# INSTRUCTIONS: Each iterations has 3 inputs. First all (hybrid) features. Second all static features and third all dynamic features #")
    f.write("############################################################################\n")
    f.close()

    # some important variables
    app_ids = {}
    app_counter = 0
    f1score = 0.0
    previous_f1score = 0.0

    ###############################################################################################################
    # Retrieve and run all the apks for the training phase
    ###############################################################################################################
    prettyPrint("Running all the apps for the Learning phase", "info2")
    input_dir = glob.glob("%s/*" % arguments.inputDirectory)

    # loop trough the goodware and malware folder
    for input_folders in input_dir:
        app_type = os.path.basename(input_folders)
        prettyPrint("Now processing all %s apps" % app_type, "info2")

        allAPKs = glob.glob("%s/%s/*.apk" % (arguments.inputDirectory, app_type))

        if len(allAPKs) < 1:
            prettyPrint("Could not find any APK's under \"%s/%s\". Exiting" % (arguments.inputDirectory, app_type),
                        "error")
            return False

        prettyPrint(
            "Successfully retrieved %s APK's from \"%s/%s\"" % (len(allAPKs), arguments.inputDirectory, app_type),
            "info2")

        # Loop through all the apk files, for the first time
        for apk in allAPKs:
            app_ids[app_counter] = {"path": apk, "malicious": 0, "features": [], "run_counter": 0}

            if app_type == "malware":
                app_ids[app_counter]['malicious'] = 1

            apk_name = os.path.basename(apk)
            prettyPrint("Now working with %s" % apk_name, "info2")

            ####################################################################
            # Create the output directories
            ####################################################################
            if not os.path.exists(arguments.outputDirectory + "/" + apk_name):
                os.makedirs(arguments.outputDirectory + "/" + apk_name)

            # create subdir for grodddroid outputs
            if not os.path.exists(arguments.outputDirectory + "/" + apk_name + "/reference/grodd_output"):
                os.makedirs(arguments.outputDirectory + "/" + apk_name + "/reference/grodd_output")

            ####################################################################
            # Restore the snapshot and start virtual machine
            ####################################################################
            prettyPrint("Restoring and starting virtual machine", "info2")
            avdIP = restore_and_start_vm(arguments.vm_name, arguments.restore_snapshot)

            ####################################################################
            # Run GroddDroid
            ####################################################################
            # change the outputdirectory for the grodddroid
            config = Config_handler(arguments.branchExplorer_dir + "/branchexp/config.ini")
            config.set_output_dir(arguments.outputDirectory + "/" + apk_name + "/reference/grodd_output/")
            config.set_max_runs('0')
            config.set_device_IP(avdIP)

            # start gordddroid
            main_cmd_call = ["python3", "-m", "branchexp.main", apk]
            result = subprocess.Popen(main_cmd_call, cwd=arguments.branchExplorer_dir).communicate()[0]

            ####################################################################
            # Extract features
            ####################################################################
            prettyPrint("Extracting numerical features ...", "info2")

            # features for the individual apk
            app_ids[app_counter]["features"] = extract_features_from_files(*get_grodd_output_file_paths(
                arguments.outputDirectory + "/" + apk_name + "/reference/grodd_output/"))

            prettyPrint("Features extracted for this specific app:", "info2")
            print(app_ids[app_counter]["features"])
            print(app_ids[app_counter]["malicious"])

            ####################################################################
            # Kill the virtual machine
            ####################################################################
            prettyPrint("Finished running this app, shutting down the virtual machine", "info2")
            shutdown_vm(arguments.vm_name)

            app_counter += 1

    ####################################################################
    # Analyze results using an svm machine learning algorithm
    ####################################################################
    print("\n\n\n")
    prettyPrint("Analyzing the results", "info2")

    # append the features of the individual apps to the overall X and y
    X, y, X_static, X_dynamic = build_machine_learning_inputs(app_ids, arguments.outputDirectory, False)

    # hybrid features - will only be logged in the results file
    do_the_machine_learning(X, y, arguments.outputDirectory + "/results.txt", arguments.selectBest,
                            arguments.kfold, 0, arguments.outputDirectory + "/ml_input.txt", 1)

    # static features - will only be logged in the results file
    do_the_machine_learning(X_static, y, arguments.outputDirectory + "/results.txt", arguments.selectBest,
                            arguments.kfold, 0, arguments.outputDirectory + "/ml_input.txt", 2)

    # dynamic features - iterate depending on the metrics of these
    predicted, metrics, misclassified_apps = do_the_machine_learning(X_dynamic, y,
                                                                     arguments.outputDirectory + "/results.txt",
                                                                     arguments.selectBest, arguments.kfold, 0,
                                                                     arguments.outputDirectory + "/ml_input.txt", 3)

    if metrics is not None:
        try:
            previous_f1score = f1score = metrics["f1score"]
        except Exception:
            prettyPrint("Error with the outputs of the machine learning", "info2")
    else:
        prettyPrint("Machine Learning did not return any metrics....Finishing", "info2")
        return 1

    ####################################################################
    # FEEDBACK CYCLE
    # Check which apps to run again, with different inputs
    ####################################################################
    print("\n\n\n")
    prettyPrint("---------------------------------------------------------------", "info2")
    prettyPrint("Running the misclassified apps again with groddroid forcing", "info2")

    run = True

    if misclassified_apps is not None:
        if f1score == 1.0 and len(misclassified_apps) == 0:
            ####################################################################
            # Exit successfully
            ####################################################################
            prettyPrint("Perfect f1score, finishing up", "info2")
            run = False
    else:
        prettyPrint("Machine Learning did not return any misclassified apps....Finishing", "info2")

    feedback_run_counter = 1
    while (run):
        if misclassified_apps is None:
            prettyPrint("No misclassified apps", "info2")
            return 1

        prettyPrint("Overall run number %s for the missclassified apps" % feedback_run_counter, "info2")

        for apk_index in misclassified_apps:
            apk = app_ids[apk_index]["path"]
            apk_name = os.path.basename(apk)

            prettyPrint("Now working with %s" % apk_name, "info2")

            ####################################################################
            # Restore the snapshot and start virtual machine
            ####################################################################
            prettyPrint("Restoring and starting virtual machine", "info2")
            avdIP = restore_and_start_vm(arguments.vm_name, arguments.restore_snapshot)

            ####################################################################
            # Run GroddDroid
            ####################################################################
            # change the outputdirectory for the grodddroid
            config = Config_handler(arguments.branchExplorer_dir + "/branchexp/config.ini")
            config.set_output_dir(arguments.outputDirectory + "/" + apk_name + "/improvement/grodd_output/")
            config.set_device_IP(avdIP)

            # set the new max number of runs grodd should do
            if app_ids[apk_index]["run_counter"] == 0:
                app_ids[apk_index]["run_counter"] += 2
            else:
                app_ids[apk_index]["run_counter"] += 1

            config.set_max_runs(str(app_ids[apk_index]["run_counter"]))

            # get the location of the stored acfg
            acfg_path = None
            if os.path.exists(arguments.outputDirectory + "/" + apk_name + "/reference/grodd_output/acfg.txt"):
                acfg_path = arguments.outputDirectory + "/" + apk_name + "/reference/grodd_output/acfg.txt"

            # start gordddroid if app did not crash before
            if acfg_path is None:
                main_cmd_call = ["python3", "-m", "branchexp.main", apk]
                result = subprocess.Popen(main_cmd_call, cwd=arguments.branchExplorer_dir).communicate()[0]
            else:
                main_cmd_call = ["python3", "-m", "branchexp.main", apk, "--acfg_path", acfg_path]
                result = subprocess.Popen(main_cmd_call, cwd=arguments.branchExplorer_dir).communicate()[0]

            # features for the individual apk
            app_ids[apk_index]["features"] = extract_features_from_files(
                *get_grodd_output_file_paths(arguments.outputDirectory + "/" + apk_name + "/improvement/grodd_output/"))

            prettyPrint("Features extracted for this specific app:", "info2")
            print(app_ids[apk_index]["features"])
            print(app_ids[apk_index]["malicious"])
            ####################################################################
            # Kill the virtual machine
            ####################################################################
            prettyPrint("Finished running this app, shutting down the virtual machine", "info2")
            shutdown_vm(arguments.vm_name)

        ####################################################################
        # Analyze results using an svm machine learning algorithm
        ####################################################################
        prettyPrint("Analyzing the results", "info2")

        # append the features of the individual apps to the overall X and y
        X, y, X_static, X_dynamic = build_machine_learning_inputs(app_ids, arguments.outputDirectory, False)

        # hybrid features - will only be logged in the results file
        do_the_machine_learning(X, y, arguments.outputDirectory + "/results.txt", arguments.selectBest,
                                arguments.kfold, feedback_run_counter, arguments.outputDirectory + "/ml_input.txt", 1)

        # static features - will only be logged in the results file
        do_the_machine_learning(X_static, y, arguments.outputDirectory + "/results.txt", arguments.selectBest,
                                arguments.kfold, feedback_run_counter, arguments.outputDirectory + "/ml_input.txt", 2)

        # dynamic features - iterate depending on the metrics of these
        predicted, metrics, misclassified_apps = do_the_machine_learning(X_dynamic, y,
                                                                         arguments.outputDirectory + "/results.txt",
                                                                         arguments.selectBest, arguments.kfold,
                                                                         feedback_run_counter,
                                                                         arguments.outputDirectory + "/ml_input.txt", 3)

        if metrics is not None:
            try:
                f1score = metrics["f1score"]
            except Exception:
                prettyPrint("", "info2")
                prettyPrint("Machine Learning did not return any metrics....Finishing", "info2")
        else:
            prettyPrint("Machine Learning did not return any metrics....Finishing", "info2")
            return 1

        # check the results and whether we should run the apps again
        if misclassified_apps is not None:
            if len(misclassified_apps) > 0:
                if previous_f1score > f1score:
                    run = False
                    prettyPrint("The results of the previous (Run %s) run were better, finishing up.." %
                                feedback_run_counter - 1, "info2")
                else:
                    previous_f1score = f1score
            else:
                run = False
                prettyPrint("TNo more misclassified apps, finishing up..", "info2")
        else:
            prettyPrint("No more misclassified apps, finishing up..", "info2")

        feedback_run_counter += 1

    ####################################################################
    # Exit successfully
    ####################################################################
    prettyPrint("Finished with everything", "info2")

    # simply save the X and Y learning feature vectors
    build_machine_learning_inputs(app_ids, arguments.outputDirectory, True)

    f = open(arguments.outputDirectory + "/results.txt", "a")
    f.write("############################################################################\n")
    f.write("# End time: %s #\n" % (getTimestamp()))
    f.write("############################################################################\n")
    f.close()

    return True


def build_machine_learning_inputs(dictionary, output_dir, extend=False):
    """Build the machine learning inputs form the features of each individual apk"""
    X, y = [], []
    for i in range(len(dictionary)):
        X.append(dictionary[i]["features"])
        y.append(dictionary[i]['malicious'])

    # build the subsets for the static and dynmaic features
    X_static = []
    for i in X:
        X_static.append(i[-33:])

    X_dynamic = []
    for i in X:
        X_dynamic.append(i[:31])

    if extend == True:
        X2 = X
        y2 = y

        if os.path.exists("X_database.txt") and os.path.exists("y_database.txt"):
            # try to load the whole database of features
            try:
                with open("X_database.txt", "rb") as file:
                    loaded_x = pickle.load(file)

                # print("LOADED FILE x")
                # print(loaded_x)

                X2 = loaded_x
                X2.extend(X)

                # print(X2)

                with open("y_database.txt", "rb") as file:
                    loaded_y = pickle.load(file)

                # print("LOADED FILE y")
                # print(loaded_y)

                y2 = loaded_y
                y2.extend(y)

                # print(y2)
            except Exception:
                pass

            # append the new featuers to the database
            with open("X_database.txt", "wb") as file:
                pickle.dump(X2, file)

            with open("y_database.txt", "wb") as file:
                pickle.dump(y2, file)

            try:
                copyfile("X_database.txt", output_dir + "/X_database.txt")
                copyfile("y_database.txt", output_dir + "/y_database.txt")
            except Exception:
                pass

            return X2, y2
        else:
            prettyPrint("No X and y database found, only working with this runs features", "info2")
            return X, y

    return X, y, X_static, X_dynamic


def get_grodd_output_file_paths(grodd_output_path):
    """Find the paths to the grodddroid output files"""
    traces_file_path = ""
    targets_file_path = ""
    to_force_file_path = ""
    stats_file_path = ""
    manifest_file_path = ""

    run_directories = os.listdir(grodd_output_path)
    run_directory = max(run_directories, key=lambda run_directories: re.split(r"_|\.", run_directories))

    if not os.path.exists(grodd_output_path + "/" + run_directory):
        prettyPrint("Output-path does not exist")
        return traces_file_path, targets_file_path, to_force_file_path, stats_file_path, manifest_file_path

    for root, dirs, files in os.walk(grodd_output_path + "/" + run_directory):
        for name in files:
            if name == "traces.log":
                traces_file_path = os.path.join(root, name)
            elif name == "targets.json":
                targets_file_path = os.path.join(root, name)
            elif name == "to_force.log":
                to_force_file_path = os.path.join(root, name)
            elif name == "stats.json":
                stats_file_path = os.path.join(root, name)

    if os.path.exists(grodd_output_path + "apktool/AndroidManifest.xml"):
        manifest_file_path = grodd_output_path + "apktool/AndroidManifest.xml"

    return traces_file_path, targets_file_path, to_force_file_path, stats_file_path, manifest_file_path


def extract_features_from_files(traces_file_path, targets_file_path, to_force_file_path, stats_file_path,
                                manifest_file_path):
    """Extract features form the manifest file, traces file and the grodddroid output files"""

    features = []

    extractor = Extractor()

    if traces_file_path:
        prettyPrint("Extracting features from the traces file ...", "info2")
        features.extend(extractor.extract_traces_features(traces_file_path))
    else:
        # set all the traces features to 0, so that we do not have an error in the machine learning
        features.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    if targets_file_path:
        prettyPrint("Extracting features from the targets file ...", "info2")
        features.extend(extractor.extract_targets_features(targets_file_path))
    else:
        # set all the targets features to 0, so that we do not have an error in the machine learning
        features.extend([0.0, 0.0, 0.0])

    if to_force_file_path:
        prettyPrint("Extracting features from the to_force file ...", "info2")
        features.append(extractor.extract_to_force_features(to_force_file_path))
    else:
        # set all the force features to 0, so that we do not have an error in the machine learning
        features.extend([0.0])

    if stats_file_path:
        prettyPrint("Extracting features from the stats file ...", "info2")
        features.extend(extractor.extract_stats_features(stats_file_path))
    else:
        # set all the stats features to 0, so that we do not have an error in the machine learning
        features.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    if manifest_file_path:
        prettyPrint("Extracting features from the manifest file ...", "info2")
        features.extend(extractor.extract_manifest_file_features(manifest_file_path))
    else:
        # set all the traces features to 0, so that we do not have an error in the machine learning
        features.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    return features


def do_the_machine_learning(X, y, output_dir, selectBest, kfold, iteration, output2_dir=None, feature_type=1):
    """Do the actual machine learning and return the results"""

    # Classifying using K-nearest neighbors
    K = [10, 15, 20, 25, 30, 35]
    metricsDict = {}
    missclassifiedDict = {}

    tmpPredicted = [0] * len(y)
    for k in K:
        prettyPrint("Classifying using K-nearest neighbors with K=%s" % k)
        predicted = predictKFoldKNN(X, y, K=k, kfold=int(kfold), selectKBest=int(selectBest))

        for i in range(len(predicted)):
            tmpPredicted[i] += predicted[i]

        metrics = calculateMetrics(y, predicted)
        metricsDict["KNN%s" % k] = metrics

        tempMissclassified = get_indices_of_misclassified_apps(y, predicted)
        missclassifiedDict["KNN%s" % k] = {"missclassified": tempMissclassified,
                                           "#crashed_apps": len(tempMissclassified)}

    # Classifying using Random Forests
    E = [10, 25, 50, 75, 100]
    for e in E:
        prettyPrint("Classifying using Random Forests with %s estimators" % e)
        predicted = predictKFoldTrees(X, y, kfold=int(kfold), selectKBest=int(selectBest))

        for i in range(len(predicted)):
            tmpPredicted[i] += predicted[i]

        metrics = calculateMetrics(y, predicted)
        metricsDict["Trees%s" % e] = metrics

        tempMissclassified = get_indices_of_misclassified_apps(y, predicted)
        missclassifiedDict["Trees%s" % e] = {"missclassified": tempMissclassified,
                                             "#crashed_apps": len(tempMissclassified)}

    # Classifying using SVM
    prettyPrint("Classifying using Support vector machines")
    predicted = predictKFoldSVM(X, y, kfold=int(kfold), selectKBest=int(selectBest))

    for i in range(len(predicted)):
        tmpPredicted[i] += predicted[i]

    metrics = calculateMetrics(y, predicted)
    metricsDict["svm"] = metrics

    tempMissclassified = get_indices_of_misclassified_apps(y, predicted)
    missclassifiedDict["svm"] = {"missclassified": tempMissclassified, "#crashed_apps": len(tempMissclassified)}

    # Average the predictions in tempPredicted
    predicted = [-1] * len(y)
    for i in range(len(tmpPredicted)):
        predicted[i] = 1 if tmpPredicted[i] >= 12.0 / 2.0 else 0  # 12 classifiers

    metricsDict["all"] = calculateMetrics(predicted, y)
    metrics = metricsDict["all"]

    missclassified_apps = get_indices_of_misclassified_apps(y, predicted)
    missclassifiedDict["all"] = {"missclassified": missclassified_apps, "#crashed_apps": len(tempMissclassified)}

    # Print and save the results:
    feature_type_string = "\n\n"
    if feature_type == 1:
        feature_type_string += "HYBRID FEATURES\n"
    elif feature_type == 2:
        feature_type_string += "STATIC FEATURES\n"
    elif feature_type == 3:
        feature_type_string += "DYNAMIC FEATURES\n"

    for m in metricsDict:
        # The average metrics for training dataset
        prettyPrint(feature_type_string, "info2")
        prettyPrint("Metrics using %s-fold cross validation and %s" % (kfold, m), "info2")
        prettyPrint("Accuracy: %s" % str(metricsDict[m]["accuracy"]), "info2")
        prettyPrint("Recall: %s" % str(metricsDict[m]["recall"]), "info2")
        prettyPrint("Specificity: %s" % str(metricsDict[m]["specificity"]), "info2")
        prettyPrint("Precision: %s" % str(metricsDict[m]["precision"]), "info2")
        prettyPrint("F1 Score: %s" % str(metricsDict[m]["f1score"]), "info2")

        # Log results to the outfile
        f = open(output_dir, "a")
        f.write(feature_type_string)
        f.write("############################################################################\n")
        f.write("# Metrics: algorithm: %s, iteration %s, timestamp: %s #\n" % (m, iteration, getTimestamp()))
        f.write("############################################################################\n")
        f.write("Validation - accuracy: %s, recall: %s, specificity: %s, precision: %s, F1-score: %s,"
                " Misclassified apps: %s, Number of misclassified apps: %s\n\n" % (
                    metricsDict[m]["accuracy"], metricsDict[m]["recall"], metricsDict[m]["specificity"],
                    metricsDict[m]["precision"], metricsDict[m]["f1score"],
                    str(missclassifiedDict[m]["missclassified"]),
                    str(missclassifiedDict[m]["#crashed_apps"])))
        f.close()

    if output2_dir is not None:
        # Log the inputs of the machine learning into a file
        f = open(output2_dir, "a")
        f.write(feature_type_string)
        f.write("############################################################################\n")
        f.write("# Machine Learning input: iteration %s, timestamp: %s #\n" % (iteration, getTimestamp()))
        f.write("############################################################################\n")
        f.write("X input: %s \n\n y input: \n %s \n\n" % (str(X), str(y)))
        f.close()

    return predicted, metrics, missclassified_apps


def restore_and_start_vm(vm_id, snapshot_name):
    """Restore the snapshot of the virtual machine and launch it"""

    # args = ['vboxmanage', 'snapshot', vm_id, 'restore', snapshot_name]
    # print(subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0])

    # leave time for restoring the snapshot
    # time.sleep(10)

    # start genymotion vm
    # args = ['open', '-a', '/Applications/Genymotion.app/Contents/MacOS/player.app', '--args', '--vm-name', vm_id]

    # Comamnd for Ubuntu machine
    # args = ["/opt/genymobile/genymotion/player", "--vm-name", vm_id]

    # subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]

    # prettyPrint("Waiting for the vrtual machine to boot up completely", "info2")

    # wait until vm is completely booted
    # time.sleep(40)



    # Aleis method
    args_snap = ['vboxmanage', 'snapshot', vm_id, 'restore', snapshot_name]
    prettyPrint("Restoring snapshot \"%s\"" % snapshot_name, "debug")
    result = subprocess.Popen(args_snap, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]
    attempts = 1

    result = str(result)
    while result.lower().find("error") != -1:
        print(result)
        # Retry restoring snapshot for 10 times and then exit
        if attempts == 25:
            prettyPrint("Failed to restore snapshot \"%s\" after 10 attempts. Exiting" % arguments.vmsnapshot, "error")
            return False
        prettyPrint(
            "Error encountered while restoring the snapshot \"%s\". Retrying ... %s" % (snapshot_name, attempts),
            "warning")

        # shut down the vm on virtual box
        args = ['vboxmanage', 'controlvm', vm_id, 'poweroff']
        subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]

        # Now attempt restoring the snapshot
        result = subprocess.Popen(args_snap, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]

        result = str(result)
        attempts += 1
        time.sleep(1)

    # 3.b. Start the Genymotion Android virtual device

    prettyPrint("Starting the Genymotion machine \"%s\"" % vm_id, "debug")

    args = ["/opt/genymobile/genymotion/player", "--vm-name", vm_id]
    genyProcess = subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    prettyPrint("Waiting for machine to boot ...", "debug")
    time.sleep(23)

    # Retrieve the IP address of the virtual device
    getAVDIPCmd = ["VBoxManage", "guestproperty", "enumerate", vm_id]
    result = subprocess.Popen(getAVDIPCmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]
    result = str(result)
    result = result.replace(' ', '')
    if result.lower().find("error") != -1:
        prettyPrint("Unable to retrieve the IP address of the AVD", "error")
        print(result)
    index = result.find("androvm_ip_management,value:") + len("androvm_ip_management,value:")
    avdIP = ""
    while result[index] != ',':
        avdIP += result[index]
        index += 1
    adbID = "%s:5555" % avdIP

    print("\n\n")
    print(str(avdIP))
    print("\n\n")

    return str(avdIP)


def shutdown_vm(vm_id):
    """Shutdown the virtual machine"""

    # Shut down the genymotion machine
    # args = ['ps', 'x']
    # p1 = subprocess.Popen(args, stdout=subprocess.PIPE)

    # args = ['grep', 'Genymotion\.app/Contents/MacOS/.*player']
    # p2 = subprocess.Popen(args, stdin=p1.stdout, stdout=subprocess.PIPE)

    # args = ['awk', '{print $1}']
    # p3 = subprocess.Popen(args, stdin=p2.stdout, stdout=subprocess.PIPE)

    # args = ['xargs', 'kill']
    # p4 = subprocess.Popen(args, stdin=p3.stdout, stdout=subprocess.PIPE)

    # p1.stdout.close()
    # p2.stdout.close()
    # p3.stdout.close()
    # p4.communicate()[0]

    # Command for Ubuntu machine
    args = ["/opt/genymobile/genymotion/player", "--poweroff", "--vm-name", vm_id]
    subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]

    if genyProcess:
        genyProcess.kill()

    time.sleep(2)

    # shut down the vm on virtual box
    args = ['vboxmanage', 'controlvm', vm_id, 'poweroff']
    subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]

    time.sleep(2)


if __name__ == "__main__":
    main()
