package io.shgck.miniapp;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * A simple receiver that starts a DummyService.
 */
public class DummyReceiver extends BroadcastReceiver {

	@Override
	public void onReceive(Context context, Intent intent) {
		Log.i("MINI", "in DummyReceiver.onReceiver, starting service");
		context.startService(new Intent(context, DummyService.class));
	}

}
