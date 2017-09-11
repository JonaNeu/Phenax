""" Find and mark suspicious / risky instructions in method CFGs.

Currently unused module. This is useful to create CFG and ACFG that are nicer to
look at in xdot, but as heuristics are applied in ForceCFI and not here, we do
not need to do it again here if we do not export the ACFG as a DOT file.
"""


def add_risk_infos(method, sigs):
    """ Search for risky stuff in nodes of a method graph and put appropriate
    risk scores as the "risk" node attributes """
    method_sig = method.signature
    title_node = method.graph.node[method_sig]

    for node_name in method.graph.nodes_iter():
        node = method.graph.node[node_name]

        # Skip non-units
        if node.get("shape", "box") != "box":
            continue

        for sig in sigs:
            sig_risk = 0

            # Check def'd classes
            used_types = node.get("used_types", "")
            used_types = used_types.split(", ") if used_types else []
            for def_type in used_types:
                for class_sig in sig["classes"]:

                    if class_sig.endswith(".*"):
                        check = def_type.startswith(class_sig[:-1])
                    else:
                        check = class_sig == def_type

                    if check:
                        score = sig["score"]
                        add_risk(node, score)
                        sig_risk += score

            # Check grep-able signatures
            label = node["label"].lower()
            for grep in sig["grep"]:
                grep = grep.lower()
                if grep in label:
                    score = sig["score"]
                    add_risk(node, score)
                    sig_risk += score

            # Print risk summary of that signature category
            if sig_risk:
                print("/!\\ Risk ({cat}, {score}) in {sig} /!\\".format(
                    cat = sig["category"],
                    score = sig_risk,
                    sig = method_sig,
                ))

        append_risk_to_label(node)

    add_risk(title_node, sum_risk(method))
    append_risk_to_label(title_node)


def add_risk(node, risk):
    """ Add the risk score to this node (add it to current score if any). """
    if not "risk" in node:
        node["risk"] = 0
    node["risk"] += risk


def sum_risk(method):
    """ Sum risk of all nodes in the method graph. """
    risk = 0
    for node_name in method.graph.nodes_iter():
        node = method.graph.node[node_name]
        if "entry_point" in node:
            continue
        if "risk" in node:
            risk += node["risk"]
    return risk


def append_risk_to_label(node):
    """ Append the risk score to the node label, as "(RS: n)". """
    node_risk = node.get("risk", 0)
    if node_risk > 0:
        node["label"] += " (RS: " + str(node_risk) + ")"

        # Change the color of non-special nodes
        if not "entry_point" in node:
            node["style"] = "filled"
            node["fillcolor"] = "orange"
