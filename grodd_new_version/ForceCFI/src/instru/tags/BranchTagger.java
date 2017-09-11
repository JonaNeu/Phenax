package instru.tags;

import instru.Main;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import org.apache.commons.lang3.mutable.MutableBoolean;

import soot.Body;
import soot.BodyTransformer;
import soot.Scene;
import soot.SootMethod;
import soot.Unit;
import soot.Value;
import soot.jimple.AbstractStmtSwitch;
import soot.jimple.IfStmt;
import soot.jimple.InvokeStmt;
import soot.jimple.Jimple;
import soot.jimple.StaticInvokeExpr;
import soot.jimple.StringConstant;

/**
 * BranchTagger is a Soot transformation that adds Log.i() entries for each
 * method entry point (BEGIN) and conditional branches (BRANCH).
 */
public class BranchTagger extends BodyTransformer {

	public enum TagType {
		METHOD, BRANCH
	}

	private static final String logSig = "<android.util.Log: int i(java.lang.String,java.lang.String)>";
	private static final String logTag = "JFL";

	private boolean onFirstUnit;
	private int nbName = 0;
	private HashMap<Unit, String> unitNames = new HashMap<Unit, String>();
	private List<String> tags = new ArrayList<String>();

	@Override
	protected void internalTransform(Body body, String phase, Map<String, String> options) {
		if (Main.is_class_useless(body.getMethod().getDeclaringClass().toString())
				|| Main.is_resource_dummy(body.getMethod().getSignature()))
			return;

		// We need to treat the first statement of a method
		onFirstUnit = true;

		Iterator<Unit> i = body.getUnits().snapshotIterator();
		while (i.hasNext()) {
			Unit unit = i.next();
			addTags(unit, body);
		}

		if (onFirstUnit)
			System.err.println("Warning: I failed to instrument this method !");
	}

	/**
	 * Add the tags for that Unit u.
	 * 
	 * @param unit
	 *            Unit to handle
	 * @param body
	 *            Body the Unit u has been taken from
	 */
	private void addTags(Unit unit, final Body body) {
		// For the first statement of a method, add a BEGIN tag.
		// This is one of the first statements of a method
		if (onFirstUnit && !unit.toString().contains(":= @this") && !unit.toString().contains(":= @parameter")) {
			Unit methodTag = addLogInfoUnit(body, unit, TagType.METHOD, false);
			tags.add("BEGIN" + unitNames.get(methodTag));
			this.onFirstUnit = false;
		}

		unit.apply(new AbstractStmtSwitch() {
			/**
			 * Conditional branches: - add a Log Unit after the condition
			 * testing (at the "then" place), - add a Log Unit before the other
			 * branch (the "else"), and redirect the condition to this new Log
			 * Unit.
			 */
			public void caseIfStmt(IfStmt stmt) {
				
				Unit firstBranch;
				if(body.getUnits().getSuccOf(stmt).toString().contains("BRANCH")){
					// There is a tag after stmt, do not insert it twice
					firstBranch = body.getUnits().getSuccOf(stmt);
				}
				else{
					// Add Log Unit directly after the condition statement.
					firstBranch = addLogInfoUnit(body, stmt, TagType.BRANCH, true);
				}

				Unit target = stmt.getTarget();
				Unit newTarget;
				if(stmt.getTarget().toString().contains("BRANCH")){
					// There is tag before the stmt target, do no insert it twice
					newTarget = target;
				}
				else{
					// Add Log Unit directly before the old "else" target and point
					// to this new Unit.
					newTarget = addLogInfoUnit(body, target, TagType.BRANCH, false);
					stmt.setTarget(newTarget);
				}

				tags.add("BRANCH" + unitNames.get(firstBranch) + "/BRANCH" + unitNames.get(newTarget));
			}
		});
//		System.out.print("Validating: " + body.getMethod().getSignature());
//		System.out.flush();
		body.validate();
//		System.out.println("Done");
//		System.out.flush();
	}

	/**
	 * Add a Log.i() Unit next to the Unit u in Body body, with the tag "JFL"
	 * and the message info.
	 * 
	 * @param unit
	 *            neighbor for the new Unit
	 * @param body
	 *            Body where to add the new Unit
	 * @param info
	 *            message to give to the Log.i() function
	 * @param after
	 *            specify whether to add the new Unit before or after u
	 * @return the generated Log.i Unit
	 */
	private Unit addLogInfoUnit(Body body, Unit unit, TagType tagType, boolean after) {
		String shortTag = newName();
		String fullTag = null;
		switch (tagType) {
		case METHOD:
			fullTag = "BEGIN" + shortTag;
			break;
		case BRANCH:
			fullTag = "BRANCH" + shortTag;
			break;
		}

		SootMethod logMethod = Scene.v().getMethod(logSig);
		Value logTagConst = StringConstant.v(logTag);
		Value logMessageConst = StringConstant.v(fullTag);

		StaticInvokeExpr invokeExpr = Jimple.v().newStaticInvokeExpr(logMethod.makeRef(), logTagConst, logMessageConst);
		Unit invokeStmt = Jimple.v().newInvokeStmt(invokeExpr);
		unitNames.put(invokeStmt, shortTag);

		if (after)
			body.getUnits().insertAfter(invokeStmt, unit);
		else
			body.getUnits().insertBefore(invokeStmt, unit);

		return invokeStmt;
	}

	/** Generate a valid name "Nxxx" (with xx a unique ID) for new tags. */
	private String newName() {
		return "N" + nbName++;
	}

	/**
	 * Direct access to the Unit to name map, return null if it doesn't contain
	 * unit.
	 */
	public String getUnitTagOrNull(Unit unit) {
		return unitNames.get(unit);
	}

	/** Write all tags added during that Soot transformation. */
	public void writeInfos() {
		File f = new File(Main.outputDir + "/all_tags.log");
		try {
			FileWriter fw = new FileWriter(f);
			for (String value : tags)
				fw.write(value + "\n");
			fw.close();
		} catch (IOException e) {
			System.err.println("Can't write in file " + f.getAbsolutePath());
		}
	}

	/**
	 * Determine if unit is a Log.i call set by addTags earlier, and that what
	 * it logs is of specified tag type.
	 * 
	 * @return true if it's a Log.i call of the correct TagType
	 */
	public static boolean isTag(Unit unit, final TagType tagType) {
		final MutableBoolean isTag = new MutableBoolean(false);

		// Several things are checked here: that unit is an InvokeStmt invoking
		// the Log.i method,
		// and it's second arg is a constant string representing a type of the
		// correct type.
		// The type check for StringConstant is because Log.i can be used with
		// dynamically built
		// Strings I guess?
		unit.apply(new AbstractStmtSwitch() {
			public void caseInvokeStmt(InvokeStmt stmt) {
				if (stmt.getInvokeExpr().getMethod().getSignature().equals(logSig)) {
					Value secondArg = stmt.getInvokeExpr().getArg(1);
					if (secondArg instanceof StringConstant) {
						String tag = ((StringConstant) secondArg).value;

						switch (tagType) {
						case METHOD:
							isTag.setValue(tag.startsWith("BEGIN"));
							break;
						case BRANCH:
							isTag.setValue(tag.startsWith("BRANCH"));
							break;
						}
					}
				}
			}
		});

		return isTag.booleanValue();
	}
}