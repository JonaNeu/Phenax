package instru.heuristics;

import org.json.simple.JSONObject;

/**
 * An Alert represents a piece of code (usually an instruction) that is typical of malware
 * behaviour, with some informations to be reused later.
 */
public class Alert {
	
	public enum AlertType {
		CLASS, GREP
	}
	
	/** Context of this alert (a class name, a suspicious String, etc) */
	public AlertType type;
	/** Heuristic that generated this alert */
	public Heuristic heuristic;
	
	/** Context of this alert (a class name, a suspicious String, etc) */
	public String context;
	/** Instruction linked to this alert (Jimple format) */
	public String instruction;
	/** Unique integer key, should come from a hash */
	public int key;
	
	/** Hint of original Java source column number for that instruction (usually not available) */
	public int sourceColumnNum;
	/** Hint of original Java source line number for that instruction */
	public int sourceLineNum;
	
	public Alert(AlertType type, Heuristic heuristic, String context, String inst, int key,
			int column, int line) {
		this.type = type;
		this.heuristic = heuristic;
		this.context = context;
		this.instruction = inst;
		this.key = key;
		this.sourceColumnNum = column;
		this.sourceLineNum = line;
	}
	
	/** One-liner for that alert. */
	public String toString() {
		StringBuilder sb = new StringBuilder();
		sb.append(heuristic.name);
		sb.append(" (RS " + heuristic.score + "): ");
		sb.append("\"" + context + "\"");
		sb.append(" in instruction: ");
		sb.append(instruction);
		sb.append(" (line " + sourceLineNum + "," + sourceColumnNum + ")");
		return sb.toString();
	}
	
	/** Return JSON representation of that Alert. */
	@SuppressWarnings("unchecked")
	public JSONObject toJson() {
		JSONObject alert = new JSONObject();
		alert.put("category", heuristic.name);
		alert.put("score", heuristic.score);
		alert.put("context", context);
		alert.put("instruction", instruction);
		alert.put("key", key);
		alert.put("source_column", sourceColumnNum);
		alert.put("source_line", sourceLineNum);
		return alert;
	}
	
	public int getKey(){
		return key;
	}
	
}