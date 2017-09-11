package instru.graphs;

import java.util.ArrayList;
import java.util.Arrays;

public class MethodSignature {
	String def_class;
	String return_type;
	String meth_name;
	ArrayList<String> params;
	ArrayList<String> calledInList = new ArrayList<String>();

	public MethodSignature(String signature) {
		signature = signature.trim();
		if (signature.startsWith("<"))
			signature = signature.substring(1);
		if (signature.endsWith(">"))
			signature = signature.substring(0, signature.length() - 1);
		int first_space = signature.indexOf(' ');
		int second_space = signature.indexOf(' ', first_space + 1);
		int open_parenth = signature.indexOf('(');
		int close_parenth = signature.indexOf(')');
		def_class = signature.substring(0, first_space - 1);
		if (def_class.startsWith("<"))
			def_class = def_class.substring(1, def_class.length());
		return_type = signature.substring(first_space + 1, second_space);

		meth_name = signature.substring(second_space + 1, open_parenth);
		String paramsString = signature.substring(open_parenth + 1, close_parenth);
		params = new ArrayList<String>();
		if (!paramsString.isEmpty())
			params = new ArrayList<String>(Arrays.asList(paramsString.split(",")));
	}

	public MethodSignature(String def_class, String return_type, String meth_name, ArrayList<String> params,
			String calledIn) {
		this.def_class = def_class;
		this.return_type = return_type;
		this.meth_name = meth_name;
		this.params = params;
		this.calledInList.add(calledIn);
	}

	@Override
	public boolean equals(Object obj) {
		// TODO Auto-generated method stub
		if (obj.getClass() != this.getClass())
			return false;
		MethodSignature ms = (MethodSignature) obj;
		if ((ms.getParams().size() == this.params.size()) && ms.getDef_class().equals(this.def_class)
				&& ms.getReturn_type().equals(this.return_type) && ms.getMeth_name().equals(this.meth_name)) {
			for (int i = 0; i < this.params.size(); i++) {
				if (!ms.getParams().get(i).equals(this.getParams().get(i)))
					return false;
			}
			return true;
		} else
			return false;
	}

	public ArrayList<String> getCalledInList() {
		return calledInList;
	}

	public void addCalledIn(String calledIn) {
		if(!this.calledInList.contains(calledIn))
				calledInList.add(calledIn);
	}

	public void addCalledIn(MethodSignature calledIn) {
		calledInList.add(calledIn.toString());
	}
	
	public void concatinateCalledInList(ArrayList<String> calledInList){
		for(String calledIn : calledInList)
			if(!this.calledInList.contains(calledIn))
				this.calledInList.add(calledIn);
	}

	public String getDef_class() {
		return def_class;
	}

	public void setDef_class(String def_class) {
		this.def_class = def_class;
	}

	public String getReturn_type() {
		return return_type;
	}

	public void setReturn_type(String return_type) {
		this.return_type = return_type;
	}

	public String getMeth_name() {
		return meth_name;
	}

	public void setMeth_name(String meth_name) {
		this.meth_name = meth_name;
	}

	public ArrayList<String> getParams() {
		return params;
	}

	public void setParams(ArrayList<String> params) {
		this.params = params;
	}

	@Override
	public String toString() {
		StringBuilder sb = new StringBuilder();
		sb.append(def_class);
		sb.append(": ");
		sb.append(return_type);
		sb.append(" ");
		sb.append(meth_name);
		sb.append("(");
		boolean first = true;
		for (int i = 0; i < params.size(); i++) {
			if (!first)
				sb.append(",");
			else
				first = false;
			sb.append(params.get(i));
		}
		sb.append(")");
		return sb.toString();
	}

	public Boolean equals(MethodSignature methodSignature) {
		if (!this.def_class.equals(methodSignature.getDef_class()))
			return false;
		if (!this.getReturn_type().equals(methodSignature.getReturn_type()))
			return false;
		if (!this.meth_name.equals(methodSignature.getMeth_name()))
			return false;
		if (this.params.size() != methodSignature.getParams().size())
			return false;
		for (int i = 0; i < this.params.size(); i++)
			if (!this.params.get(i).equals(methodSignature.getParams().get(i)))
				return false;

		// The two method signatures are equal
		return true;
	}
}
