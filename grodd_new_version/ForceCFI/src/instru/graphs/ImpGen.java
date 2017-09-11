package instru.graphs;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.UnsupportedEncodingException;
import java.io.Writer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map.Entry;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.apache.commons.lang3.StringUtils;

import instru.Main;
import soot.Scene;
import soot.SootClass;
import soot.SootMethod;
import soot.util.HashChain;

public class ImpGen {

	public static final int CORES = Runtime.getRuntime().availableProcessors();

	private HashMap<SootClass, HashSet<SootClass>> allSupSoot = new HashMap<SootClass, HashSet<SootClass>>();
	private HashMap<String, HashSet<String>> allSup = new HashMap<String, HashSet<String>>();
	private ArrayList<MethodSignature> methodSigs = new ArrayList<MethodSignature>();
	private ArrayList<MethodSignature> invokeSigs = new ArrayList<MethodSignature>();
	private ArrayList<EdgeMinerRule> rules = new ArrayList<EdgeMinerRule>();
	private ArrayList<InterProcEdge> interProcEdges = new ArrayList<InterProcEdge>();
	// sup classes just for explicitly invoked methods
	private HashSet<String> allTypes = new HashSet<String>();
	private int nbr_add_imp_edges = 0;

	private static ImpGen instance = null;

	private ImpGen() {
		// Exists only to defeat instantiation.
	}

	public static ImpGen v() {
		if (instance == null) {
			instance = new ImpGen();
		}
		return instance;
	}

	public HashSet<SootClass> setSup(SootClass sootClass) {
		// Avoid sup recalculation if it is already calculated
		if (allSupSoot.containsKey(sootClass))
			return allSupSoot.get(sootClass);

		HashSet<SootClass> toReturn = new HashSet<SootClass>();
		HashChain<SootClass> interfaces = (HashChain<SootClass>) sootClass.getInterfaces();
		HashSet<SootClass> oneLevelSup = new HashSet<SootClass>();
		Iterator<SootClass> it = interfaces.iterator();
		while (it.hasNext()) {
			SootClass next = it.next();
			if (!next.getName().contains("android.support"))
				oneLevelSup.add(next);
		}

		if (sootClass.hasSuperclass())
			if (!sootClass.getSuperclass().getName().contains("android.support"))
				oneLevelSup.add(sootClass.getSuperclass());

		it = oneLevelSup.iterator();
		while (it.hasNext())
			toReturn.add(it.next());

		for (SootClass next : oneLevelSup) {
			HashSet<SootClass> nextSup;
			if (!allSupSoot.containsKey(next))
				nextSup = setSup(next);
			else
				nextSup = allSupSoot.get(next);
			toReturn.addAll(nextSup);
		}

		allSupSoot.put(sootClass, toReturn);

		HashSet<String> strHashSet = new HashSet<String>();
		strHashSet.add(sootClass.toString());
		allTypes.add(sootClass.toString());
		for (SootClass cls : toReturn) {
			strHashSet.add(cls.toString());
			allTypes.add(cls.toString());
		}
		allSup.put(sootClass.toString(), strHashSet);

		return toReturn;
	}

	public void genInterProcEdges(String edgeMinerFile, String impEdgesFiles) {
		System.out.println("Generating implicit edges");
		loadEdgeMinerRules(edgeMinerFile);
		removeUseless();

		// Begin Debug
		Main.debug("Sup entries : " + allSup.size());
		Main.debug("Nbr rules : " + rules.size());
		// for (EdgeMinerRule rule : rules) {
		// Main.debug(" * " + rule);
		// }

		Main.debug("allTypes : " + allTypes.size());
		Main.debug("Method signatures : " + methodSigs.size());
		Main.debug("Invoke signatures : " + invokeSigs.size());
		// End Debug

		// Multithread processing
		ExecutorService executor = Executors.newFixedThreadPool(CORES);
		for (int i = 1; i <= CORES; i++) {
			int fromIndex = (i - 1) * (invokeSigs.size() / CORES);
			int toIndex = 0;
			if (i == CORES)
				toIndex = invokeSigs.size();
			else
				toIndex = i * (invokeSigs.size() / CORES);

			Runnable worker = new RunGen(i, new ArrayList<MethodSignature>(invokeSigs.subList(fromIndex, toIndex)));
			executor.execute(worker);
		}
		executor.shutdown();
		// Wait until all threads are finish
		while (!executor.isTerminated()) {

		}

		// Remove redundant rules
		removeRedundantEdges();

		impEdgesToFile(impEdgesFiles);

		// Just for debugging
		Main.debug("Sup entries : " + allSup.size());
		Main.debug("Nbr rules : " + rules.size());
		Main.debug("allTypes : " + allTypes.size());
		Main.debug("Method signatures : " + methodSigs.size());
		Main.debug("Invoke signatures : " + invokeSigs.size());
		Main.debug("Generated implicit edges : " + nbr_add_imp_edges);
		// Main.debug("allSup[String] : " +
		// allSup.get("java.lang.String"));
		// if (!methodSigs.isEmpty())
		// Main.debug("methodSigs[0] : " + methodSigs.get(0));
		// else
		// Main.debug("methodSigs is empty");
		// if (!invokeSigs.isEmpty())
		// Main.debug("invokeSigs[0] : " + invokeSigs.get(0));
		// else
		// Main.debug("invokeSigs is empty");
		// for (String s : allTypes) {
		// Main.debug("allTypes[0] : " + s);
		// break;
		// }
		// if (!rules.isEmpty())
		// Main.debug("edgeMiner[0] : " + rules.get(0));
		// else
		// Main.debug("edgeMiner is empty");
		// End Debug
	}

	/**
	 * Remove useless edgeMiner rules, method signatures and invoke signatures.
	 */
	private void removeUseless() {
		Main.debug("Remove useless rules, invokes and method signatures .. ");
		System.out.flush();

		// Remove useless EdgeMiner rules
		Main.debug("Removing useless rules ..");
		System.out.flush();
		final ArrayList<EdgeMinerRule> newRules = new ArrayList<EdgeMinerRule>();
		// Multithread processing
		ExecutorService executor_1 = Executors.newFixedThreadPool(CORES);
		for (int i = 1; i <= CORES; i++) {
			int fromIndex = (i - 1) * (rules.size() / CORES);
			int toIndex = 0;
			if (i == CORES)
				toIndex = rules.size();
			else
				toIndex = i * (rules.size() / CORES);

			Runnable worker = new Runnable() {
				private ArrayList<EdgeMinerRule> localRules;
				private int threadNumber;

				private Runnable init(int threadNumber, ArrayList<EdgeMinerRule> localRules) {
					this.localRules = localRules;
					this.threadNumber = threadNumber;
					return this;
				}

				@Override
				public void run() {
					for (EdgeMinerRule rule : localRules) {

						// Check if there is an invoke that matches the rule's
						// registration
						boolean brk = false;
						for (MethodSignature invokeSig : invokeSigs) {
							if (invokeSig.getMeth_name().equals(rule.getRegistration().getMeth_name())
									&& invokeSig.getParams().size() == rule.getRegistration().getParams().size()
									&& invokeSig.getReturn_type().equals(rule.getRegistration().getReturn_type())
									&& sup(invokeSig.getDef_class()).contains(rule.getRegistration().getDef_class())) {
								boolean pInvoke = true;
								for (int i = 0; i < invokeSig.getParams().size(); i++) {
									if (!sup(invokeSig.getParams().get(i))
											.contains(rule.getRegistration().getParams().get(i))) {
										pInvoke = false;
										break;
									}
								}
								if (!pInvoke)
									continue;

								// Check if there is a method signature that
								// matches the rule's callback
								for (MethodSignature methSig : methodSigs) {
									if (methSig.getMeth_name().equals(rule.getCallback().getMeth_name())
											&& methSig.getParams().size() == rule.getCallback().getParams().size()
											&& methSig.getReturn_type().equals(rule.getCallback().getReturn_type())
											&& sup(methSig.getDef_class())
													.contains(rule.getCallback().getDef_class())) {
										boolean pCallback = true;
										for (int i = 0; i < methSig.getParams().size(); i++) {
											if (!sup(methSig.getParams().get(i))
													.contains(rule.getCallback().getParams().get(i))) {
												pCallback = false;
												break;
											}
										}
										if (pCallback) {
											synchronized (ImpGen.class) {
												newRules.add(rule);
											}
											brk = true;
											break;
										}
									}
								}
							}
							if (brk)
								break;
						}
					}
				}

			}.init(i, new ArrayList<EdgeMinerRule>(rules.subList(fromIndex, toIndex)));

			executor_1.execute(worker);
		}
		executor_1.shutdown();
		// Wait until all threads are finish
		while (!executor_1.isTerminated()) {

		}
		Main.debug(newRules.size() + " rule(s) remained from " + rules.size());
		rules = newRules;

		// Remove useless invokes
		Main.debug("Removing useless invokes ..");
		System.out.flush();
		final ArrayList<MethodSignature> newInvokeSigs = new ArrayList<MethodSignature>();
		// Multithread processing
		ExecutorService executor_2 = Executors.newFixedThreadPool(CORES);
		for (int i = 1; i <= CORES; i++) {
			int fromIndex = (i - 1) * (invokeSigs.size() / CORES);
			int toIndex = 0;
			if (i == CORES)
				toIndex = invokeSigs.size();
			else
				toIndex = i * (invokeSigs.size() / CORES);

			Runnable worker = new Runnable() {
				private ArrayList<MethodSignature> localInvokeSigs;
				private int threadNumber;

				private Runnable init(int threadNumber, ArrayList<MethodSignature> localInvokeSigs) {
					this.localInvokeSigs = localInvokeSigs;
					this.threadNumber = threadNumber;
					return this;
				}

				@Override
				public void run() {
					for (MethodSignature invokeSig : localInvokeSigs) {
						for (EdgeMinerRule rule : rules) {
							if (invokeSig.getMeth_name().equals(rule.getRegistration().getMeth_name())
									&& invokeSig.getParams().size() == rule.getRegistration().getParams().size()
									&& invokeSig.getReturn_type().equals(rule.getRegistration().getReturn_type())
									&& sup(invokeSig.getDef_class()).contains(rule.getRegistration().getDef_class())) {
								boolean pInvoke = true;
								for (int i = 0; i < invokeSig.getParams().size(); i++) {
									if (!sup(invokeSig.getParams().get(i))
											.contains(rule.getRegistration().getParams().get(i))) {
										pInvoke = false;
										break;
									}
								}
								if (!pInvoke)
									continue;

								synchronized (ImpGen.class) {
									newInvokeSigs.add(invokeSig);
								}
								break;
							}
						}
					}
				}

			}.init(i, new ArrayList<MethodSignature>(invokeSigs.subList(fromIndex, toIndex)));

			executor_2.execute(worker);
		}
		executor_2.shutdown();
		// Wait until all threads are finish
		while (!executor_2.isTerminated()) {
		}
		Main.debug(newInvokeSigs.size() + " invoke(s) remained from " + invokeSigs.size());
		invokeSigs = newInvokeSigs;

		// Remove useless methods
		Main.debug("Removing useless methods ..");
		System.out.flush();
		final ArrayList<MethodSignature> newMethodSigs = new ArrayList<MethodSignature>();
		// Multithread processing
		ExecutorService executor_3 = Executors.newFixedThreadPool(CORES);
		for (int i = 1; i <= CORES; i++) {
			int fromIndex = (i - 1) * (methodSigs.size() / CORES);
			int toIndex = 0;
			if (i == CORES)
				toIndex = methodSigs.size();
			else
				toIndex = i * (methodSigs.size() / CORES);

			Runnable worker = new Runnable() {
				private ArrayList<MethodSignature> localMethodSigs;
				private int threadNumber;

				private Runnable init(int threadNumber, ArrayList<MethodSignature> localMethodSigs) {
					this.localMethodSigs = localMethodSigs;
					this.threadNumber = threadNumber;
					return this;
				}

				@Override
				public void run() {
					for (MethodSignature methSig : localMethodSigs) {
						String subMethSig = methSig.toString().substring(methSig.toString().indexOf(":") + 2);
						for (EdgeMinerRule rule : rules) {
							if (rule.getCallback().toString().substring(rule.getCallback().toString().indexOf(":") + 2)
									.equals(subMethSig)) {
								synchronized (ImpGen.class) {
									newMethodSigs.add(methSig);
								}
								break;
							}
						}
					}
				}

			}.init(i, new ArrayList<MethodSignature>(methodSigs.subList(fromIndex, toIndex)));

			executor_3.execute(worker);
		}
		executor_3.shutdown();
		// Wait until all threads to finish
		while (!executor_3.isTerminated()) {

		}
		Main.debug(newMethodSigs.size() + " method signature(s) remained from " + methodSigs.size());
		methodSigs = newMethodSigs;

		Main.debug("done");
		System.out.flush();
	}

	/**
	 * Remove redundant edges from the final results, this occur when invokes
	 * have the same signatures The goal from that is to prevent adding two
	 * implicit edges between nodes
	 */
	private void removeRedundantEdges() {
		Main.debug("Removing redundant edges");
		System.out.flush();

		ArrayList<InterProcEdge> newEdges = new ArrayList<InterProcEdge>();

		for (InterProcEdge edge : interProcEdges) {
			if (!newEdges.contains(edge))
				newEdges.add(edge);
		}
		Main.debug(newEdges.size() + " rule(s) remained from " + interProcEdges.size());
		interProcEdges = newEdges;
	}

	private ArrayList<String> sup(String type) {
		if (allSup.containsKey(type))
			return new ArrayList<String>(allSup.get(type));
		else
			return new ArrayList<String>();
	}

	public void allSupToFile(String file) {
		Main.debug("Writing allSup to file " + file + " .. ");
		try (Writer writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(file), "utf-8"))) {
			StringBuilder sb;
			for (Entry<SootClass, HashSet<SootClass>> entry : allSupSoot.entrySet()) {
				sb = new StringBuilder();
				sb.append(entry.getKey()).toString();
				sb.append(" ");
				for (SootClass sup : entry.getValue()) {
					sb.append(sup.toString());
					sb.append(" ");
				}
				sb.append("\n");
				writer.write(sb.toString());
			}
			writer.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		Main.debug("done");
	}

	private void impEdgesToFile(String file) {
		System.out.print("Writing " + nbr_add_imp_edges + " implicit edges to file " + file + " .. ");
		try (Writer writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(file), "utf-8"))) {
			writer.write("Rules:\n");
			int i = 0;
			for (EdgeMinerRule rule : rules) {
				writer.write(i + "#" + rule + "\n");
				i++;
			}
			writer.write("Implicit edges:\n");
			StringBuilder sb;
			for (InterProcEdge ie : interProcEdges) {
				sb = new StringBuilder();
				sb.append( ie.ruleIndex + " { ");
				Boolean first = true;
				for (String calledIn : ie.getRegistration().getCalledInList()) {
					if (first) {
						first = false;
					}else{
						sb.append(" @ ");						
					}
					sb.append(calledIn);
				}
				sb.append(" } -> ");

				sb.append(ie.getRegistration());
				sb.append(" -> ");
				sb.append(ie.getCallback());
				sb.append("\n");
				writer.write(sb.toString());
			}
			writer.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	public void addMethodSignature(SootMethod method) {
		// if (!method.toString().contains("android.support")) {
		MethodSignature sigMethod = new MethodSignature(method.toString());
		if (isMethodOverridden(method.getDeclaringClass(),
				method.toString().substring(method.toString().indexOf(":") + 2))) {
			addSignatureSup(sigMethod);
			methodSigs.add(sigMethod);
		}
		// }
	}

	/**
	 * Check if the method is overriding another method of a super class or an
	 * interface
	 * 
	 * @param decClass
	 *            The declaring class of the method
	 * @param subSig
	 *            the part from the position of ":" + 2 to the end of the method
	 *            signature
	 * @return True if the method is Overriding another method, false else
	 */
	private boolean isMethodOverridden(SootClass decClass, String subSig) {
		for (SootClass inter : decClass.getInterfaces()) {
			if (inter.isLibraryClass()) {
				for (SootMethod imeth : inter.getMethods()) {
					if (imeth.toString().substring(imeth.toString().indexOf(":") + 2).equals(subSig))
						return true;
				}
			}
			if (isMethodOverridden(inter, subSig))
				return true;
		}
		if (decClass.hasSuperclass()) {
			if (decClass.getSuperclass().isLibraryClass()) {
				for (SootMethod sMeth : decClass.getSuperclass().getMethods()) {
					if (sMeth.toString().substring(sMeth.toString().indexOf(":") + 2).equals(subSig))
						return true;
				}
			}
			if (isMethodOverridden(decClass.getSuperclass(), subSig))
				return true;
		}
		return false;
	}

//	public void addInvokeSignature(String signature) {
//		MethodSignature sigMethod = new MethodSignature(signature);
//		addInvokeSignature(sigMethod);
//	}

	public void addInvokeSignature(MethodSignature sigMethod) {
		addSignatureSup(sigMethod);
		Boolean found = false;
		for(MethodSignature sig : invokeSigs){
			if (sigMethod.equals(sig)){
				found = true;
				sig.concatinateCalledInList(sigMethod.getCalledInList());
			}
		}
		if(!found)
			invokeSigs.add(sigMethod);
	}

	public void addSignatureSup(MethodSignature signature) {
		setSup(Scene.v().getSootClass(signature.getDef_class()));
		setSup(Scene.v().getSootClass(signature.getReturn_type()));
		for (String p : signature.getParams()) {
			setSup(Scene.v().getSootClass(p));
		}
	}

	public void loadEdgeMinerRules(String file) {
		System.out.println("Number of method sigs before loading impEdgeFile: " + methodSigs.size());
		Main.debug("Loading EdgeMiner file " + file + " .. ");
		System.out.flush();
		try {
			BufferedReader reader = new BufferedReader(new FileReader(file));
			String line = null;

			while ((line = reader.readLine()) != null) {
				int firstCharp = line.indexOf('#');
				int secondCharp = line.indexOf('#', firstCharp + 1);
				String posStr = line.substring(secondCharp + 1, line.length());
				if (firstCharp > 0 || secondCharp > 0 || (StringUtils.isNumeric(posStr))
						|| secondCharp > firstCharp + 1) {
					String registration = line.substring(0, firstCharp);
					String callback = line.substring(firstCharp + 1, secondCharp);

					int position = Integer.parseInt(posStr);
					MethodSignature registrationM = new MethodSignature(registration);
					if (isSigInAllTypes(registrationM)) {
						MethodSignature callbackM = new MethodSignature(callback);
						if (isSigInAllTypes(callbackM) && relevant_rule_callback(callbackM)) {
							EdgeMinerRule aRule = new EdgeMinerRule(registrationM, callbackM, position);
							rules.add(aRule);
						}
					}
				} else {
					System.err.println("Error: " + file + " of unknown format, line: " + line);
					System.err.println("Exiting program");
					System.exit(-1);
				}
			}
			System.out.println(rules.size() + " rules loaded");
			reader.close();
		} catch (NumberFormatException | IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

		// TODO: Debug, remove writing to file
		try (Writer writer = new BufferedWriter(
				new OutputStreamWriter(new FileOutputStream(Main.superDir + "/rules.txt"), "utf-8"))) {
			for (EdgeMinerRule rule : rules) {
				writer.write(rule + "\n");
			}
			writer.close();
		} catch (UnsupportedEncodingException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

		Main.debug("done");
		System.out.flush();
	}

	private boolean isSigInAllTypes(MethodSignature signature) {
		if ((!allTypes.contains(signature.getDef_class())) || (!allTypes.contains(signature.getReturn_type())))
			return false;
		for (String p : signature.getParams())
			if (!allTypes.contains(p))
				return false;
		return true;
	}

	private void handle_implicit_edges(MethodSignature sigInvoke) {
		if (!can_be_registration(sigInvoke))
			return;

		for (MethodSignature sigCallee : methodSigs) {
			int ruleIndex = match(sigInvoke, sigCallee);
			if ( ruleIndex >= 0) {
				// Synchronize access between threads
				synchronized (ImpGen.class) {
					interProcEdges.add(new InterProcEdge(sigInvoke, sigCallee, ruleIndex));
					nbr_add_imp_edges += 1;
				}
			}
		}
	}

	private int match(MethodSignature sigInvoke, MethodSignature sigCallee) {
		int i = 0;
		for (EdgeMinerRule rule : rules) {
			if (compSig(rule.getRegistration(), sigInvoke, true) && compSig(rule.getCallback(), sigCallee, false)
					&& compPos(sigInvoke, sigCallee, rule.getPosition())) {
				// Main.debug("*> Match rule: " + rule);
				// Main.debug("With implicit edge: " + sigInvoke + "
				// -->" + sigCallee);
				// System.out.flush();
				return i;
			}
			i++;
		}
		return -1;
	}

	private boolean compSig(MethodSignature sigRule, MethodSignature sigApp, boolean covariant) {
		if ((sigRule.getParams().size() != sigApp.getParams().size())
				|| (!sigRule.getMeth_name().equals(sigApp.getMeth_name()))
				|| (!sup(sigApp.getDef_class()).contains(sigRule.getDef_class()))
				|| (!sup(sigApp.getReturn_type()).contains(sigRule.getReturn_type())))
			return false;
		for (int i = 0; i < sigRule.getParams().size(); i++) {
			// Comparing registration methods
			if (covariant && (!sup(sigApp.getParams().get(i)).contains(sigRule.getParams().get(i))))
				return false;
			// Comparing callback methods
			if ((!covariant) && (!sigApp.getParams().get(i).equals(sigRule.getParams().get(i))))
				return false;
		}
		return true;
	}

	private boolean compPos(MethodSignature sigCaller, MethodSignature sigCallee, int pos) {
		String pos_class = "";
		if (pos == 0)
			pos_class = sigCaller.getDef_class();
		else {
			if (pos > sigCaller.getParams().size())
				return false;
			else
				pos_class = sigCaller.getParams().get(pos - 1);
		}
			
		if (sup(sigCallee.getDef_class()).contains(pos_class))
			return true;
		else
			return false;
	}

	private boolean relevant_rule_callback(MethodSignature rule_callee) {
		// FIXME: There are many useless callbacks like toString
		if (rule_callee.getMeth_name().equals("toString") || rule_callee.getMeth_name().equals("hashCode")
				|| rule_callee.getMeth_name().equals("equals"))
			return false;

		// Eliminate methods that are not in EdgeMiner callbacks rule
		for (MethodSignature methSig : methodSigs) {
			if (rule_callee.getMeth_name().equals(methSig.getMeth_name())
					&& rule_callee.getParams().size() == methSig.getParams().size()
					&& rule_callee.getReturn_type().equals(methSig.getReturn_type())
					&& sup(methSig.getDef_class()).contains(rule_callee.getDef_class())) {
				boolean equal = true;
				for (int i = 0; i < rule_callee.getParams().size(); i++) {
					if (!rule_callee.getParams().get(i).equals(methSig.getParams().get(i))) {
						equal = false;
						break;
					}
				}
				if (equal)
					return true;
			}
		}
		return false;
	}

	private boolean can_be_callback(MethodSignature callback) {
		// Eliminate methods that have only Object as super type, and do not
		// extend its methods
		if (has_one_sup(callback))
			if ((!callback.getMeth_name().equals("clone")) && (!callback.getMeth_name().equals("equals"))
					&& (!callback.getMeth_name().equals("finalize")) && (!callback.getMeth_name().equals("getClass"))
					&& (!callback.getMeth_name().equals("hashCode")) && (!callback.getMeth_name().equals("notify"))
					&& (!callback.getMeth_name().equals("notifyAll")) && (!callback.getMeth_name().equals("toString"))
					&& (!callback.getMeth_name().equals("wait")))
				return false;
		return true;
	}

	private boolean has_one_sup(MethodSignature signature) {
		if (sup(signature.getDef_class()).size() == 2)
			return true;
		else
			return false;
	}

	private boolean can_be_registration(MethodSignature caller) {
		for (EdgeMinerRule rule : rules) {
			if (rule.getRegistration().getMeth_name().equals(caller.getMeth_name())
					&& rule.getRegistration().getParams().size() == caller.getParams().size()) {
				boolean paramsEqual = true;
				for (int i = 0; i < caller.getParams().size(); i++) {
					if (!sup(caller.getParams().get(i)).contains(rule.getRegistration().getParams().get(i))) {
						paramsEqual = false;
						break;
					}
				}
				if (paramsEqual)
					return true;
			}
		}
		return false;
	}

	private class InterProcEdge {
		private MethodSignature registration;
		private MethodSignature callback;
		int ruleIndex;

		public InterProcEdge(MethodSignature registration, MethodSignature callback, int ruleIndex) {
			this.registration = registration;
			this.callback = callback;
			this.ruleIndex= ruleIndex;
		}

		public MethodSignature getRegistration() {
			return registration;
		}

		public void setRegistration(MethodSignature registration) {
			this.registration = registration;
		}

		public MethodSignature getCallback() {
			return callback;
		}

		public void setCallback(MethodSignature callback) {
			this.callback = callback;
		}

		@Override
		public boolean equals(Object obj) {
			// TODO Auto-generated method stub
			if (obj.getClass() != this.getClass())
				return false;

			InterProcEdge edge = (InterProcEdge) obj;
			if (edge.getRegistration().equals(this.getRegistration())
					&& (edge.getCallback().equals(this.getCallback())))
				return true;
			else
				return false;
		}
	}

	private class EdgeMinerRule {
		private MethodSignature registration;
		private MethodSignature callback;
		private int position;

		public EdgeMinerRule(MethodSignature registration, MethodSignature callback, int position) {
			this.registration = registration;
			this.callback = callback;
			this.position = position;
		}

		public MethodSignature getRegistration() {
			return registration;
		}

		public void setRegistration(MethodSignature registration) {
			this.registration = registration;
		}

		public MethodSignature getCallback() {
			return callback;
		}

		public void setCallback(MethodSignature callback) {
			this.callback = callback;
		}

		public int getPosition() {
			return position;
		}

		public void setPosition(int position) {
			this.position = position;
		}

		@Override
		public String toString() {
			return registration + "#" + callback + "#" + position;
		}
	}

	private class RunGen implements Runnable {
		private ArrayList<MethodSignature> localInvokeSigs;
		private int threadNumber;

		public RunGen(int threadNumber, ArrayList<MethodSignature> localInvokeSigs) {
			this.localInvokeSigs = localInvokeSigs;
			this.threadNumber = threadNumber;
		}

		@Override
		public void run() {
			for (MethodSignature sigInvoke : localInvokeSigs) {
				ImpGen.this.handle_implicit_edges(sigInvoke);
			}
		}

	}
}