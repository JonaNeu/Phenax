package instru.heuristics;

import java.util.ArrayList;
import java.util.List;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;

public class Heuristic {

	public String name = "";
	public String description = "";
	public List<String> classes = new ArrayList<>(); 
	public List<String> greppable = new ArrayList<>(); 
	public double score = 0;
	
	public Heuristic(JSONObject json) {
		name = (String) json.get("category");
		description = (String) json.get("description");
		classes = loadStringList((JSONArray) json.get("classes"));
		greppable = loadStringList((JSONArray) json.get("grep"));
		score = ((Long) json.get("score")).doubleValue();
	}
	
	private static List<String> loadStringList(JSONArray array) {
		List<String> list = new ArrayList<>();
		for (Object obj : array) {
			String s = (String) obj;
			list.add(s);
		}
		return list;
	}
	
}
