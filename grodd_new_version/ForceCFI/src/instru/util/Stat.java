package instru.util;

public class Stat {
	
	public int nbJFLNodesWithSeenInstructions = 0;
	public int nbJFLNodes = 0;
	@Override
	public String toString() {
		return "" + nbJFLNodesWithSeenInstructions + " / " + nbJFLNodes;
	}
	
	

}
