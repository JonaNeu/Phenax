package io.shgck.miniapp;

import java.util.Calendar;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.View;

public class MainActivity extends Activity {

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_main);
		
		// Dummy example of a conditional trigger
		Calendar c = Calendar.getInstance(); 
		int seconds = c.get(Calendar.SECOND);
		if (seconds == 61)
			Log.i("MINI", "In MainActivity.onCreate: weird condition triggered!");
		else
			Log.i("MINI", "In MainActivity.onCreate: nothing happened");
	}
	
	public void dummyClick(View view) {
		Log.i("MINI", "In MainActivity.dummyClick");
		Intent intent = new Intent(this, SecondActivity.class);
		startActivity(intent);
	}

}
