package instru.force;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import soot.Body;
import soot.BodyTransformer;
import soot.Unit;
import soot.jimple.AbstractStmtSwitch;
import soot.jimple.GotoStmt;
import soot.jimple.IfStmt;
import soot.jimple.Jimple;

/**
 * Soot transformation that takes a list of branches to force and modify the app control flow to
 * force the execution of said branches.
 */
public class BranchForcer extends BodyTransformer {

	private String branchesFile = "";
	private List<String> branchesToForce = new ArrayList<String>();
	
	/**
	 * @param branchesFile file containing branches name to force
	 */
	public BranchForcer(String branchesFile) {
		this.branchesFile = branchesFile;
		loadBranchList();
	}

	@Override
	protected void internalTransform(Body body, String phase, Map<String, String> options) {
		Iterator<Unit> i = body.getUnits().snapshotIterator();
		
		while (i.hasNext()) {
			Unit u = i.next();
			inspectUnit(u, body);
		}
	}

	/**
	 * Loads the branch names in branchesFile. 
	 */
	private void loadBranchList() {
		File f = new File(branchesFile);
		try {
			BufferedReader br = new BufferedReader(new FileReader(f));
			String line;
			while ((line = br.readLine()) != null)
				branchesToForce.add(line);
			br.close();
		} catch (FileNotFoundException e) {
			System.err.println("No readable branch list file at " + branchesFile);
			e.printStackTrace();
		} catch (IOException e) {
			System.err.println("Error while reading " + branchesFile);
			e.printStackTrace();
		}
	}
	
	/**
	 * Inspect Unit u in body b. If it detects a branch that has to be forced, it modifies it. 
	 * 
	 * If I understood correctly... Jimple ifs are very similar to assembly ifs, that is:
	 * 
	 *     if (cond) {
	 *         goto some statement later
	 *     } else {
	 *         just go to the next statement (successor)
	 *     }
	 * 
	 * That means that if we want to force the first branch (the "then"), we have to force the jump,
	 * that is replacing the condition with "if true". If we want to force the other branch
	 * (the "else"), we have to ignore the jump with "if false". Now it's testing time.
	 * 
	 * @param u
	 * @param body
	 */
	private void inspectUnit(Unit u, final Body body) {
		
		u.apply(new AbstractStmtSwitch() {
			
			public void caseIfStmt(IfStmt stmt) {
				Unit branch1 = body.getUnits().getSuccOf(stmt);
				Unit branch2 = stmt.getTargetBox().getUnit();
				
				if (isBranchToForce(branch1)) {
					GotoStmt gotoStmt = Jimple.v().newGotoStmt(branch1);
					body.getUnits().swapWith(stmt, gotoStmt);
				}
				else if (isBranchToForce(branch2)) {
					GotoStmt gotoStmt = Jimple.v().newGotoStmt(branch2);
					body.getUnits().swapWith(stmt, gotoStmt);
				}
				
			}  // end of caseIfStmt
			
		});
		
		body.validate();
	}
	
	/**
	 * Returns true if the given Unit represents a branch that has to be forced. 
	 * @param branch
	 */
	private boolean isBranchToForce(Unit branch) {
		String str = branch.toString();
		if (str.contains("BRANCHN"))                      // First quick check if it's a branch tag. 
			for (String branchToForce : branchesToForce)  // If so, search if we have to force it.
				if (str.contains(branchToForce))
					return true;
		return false;
	}
	
}
