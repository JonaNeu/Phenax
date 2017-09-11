package instru.heuristics;

import instru.heuristics.Alert.AlertType;

import java.util.ArrayList;
import java.util.List;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;

import soot.Unit;

/**
 * A CodeTarget represent a piece of code that is worth noting for further inspection. A method
 * signature is attached to the target with a list of Alerts that makes this method worthy of
 * interest. 
 */
public class CodeTarget {
	
	private String methodSignature;
	private List<Alert> alerts = new ArrayList<>();
	private double riskScore = 0; 
	
	public CodeTarget(String signature) {
		methodSignature = signature;
	}
	
	/** Add a new Alert to this CodeTarget and update the total risk score. */
	public void addAlert(AlertType alertType, Heuristic heuristic, String context, Unit unit) {
		alerts.add(new Alert(
			alertType, heuristic, context,
			unit.toString(),
			unit.hashCode(),
			unit.getJavaSourceStartColumnNumber(),
			unit.getJavaSourceStartLineNumber()
		));
		riskScore += heuristic.score;
	}
	
	/** Multiple line summary of that method. */
	public String toString() {
		StringBuilder sb = new StringBuilder();
		sb.append("In method " + methodSignature + "\n");
		for (Alert alert : alerts)
			sb.append("\t" + alert.toString() + "\n");
		sb.append("Method risk score: " + riskScore + "\n");
		return sb.toString();
	}
	
	/** Return JSON representation of that CodeTarget (including all alerts). */
	@SuppressWarnings("unchecked")
	public JSONObject toJson() {
		JSONObject target = new JSONObject();
		target.put("method", methodSignature);
		target.put("score", riskScore);
		JSONArray alertsJsonList = new JSONArray();
		for (Alert alert : alerts)
			alertsJsonList.add(alert.toJson());
		target.put("alerts", alertsJsonList);
		return target;
	}
	
	public List<Alert> getAlerts(){
		return alerts;
	}
	
}
