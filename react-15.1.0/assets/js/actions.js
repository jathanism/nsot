import { browserHistory } from 'react-router';
import {CALL_API} from 'redux-api-middleware';

import Api from './api';

const client = new Api();

/* UI */

export function submittingChanged(isSubmitting) {
  return {
    type: 'IS_SUBMITTING',
    isSubmitting
  }
}

export function showSuccessNotification(message) {
  return {
    type: 'SHOW_NOTIFICATION',
    status: 'SUCCESS',
    message
  }
}

export function showFailureNotification(message) {
  return {
    type: 'SHOW_NOTIFICATION',
    status: 'FAILURE',
    message
  }
}

export function urlRedirect(url) {
  return (dispatch, getState) => {
    console.log('Redirecting to:', url);
    browserHistory.push(url);
  }
}

/* DEVICES */

export function showDeviceResult(jsonResult) {
  return {
    type: 'DEVICE_DETAIL',
    device: jsonResult
  };
}

export function showDevicesResult(jsonResult) {
  return {
    type: 'DEVICE_LIST',
    rows: jsonResult
  };
}

export function _loadDevice(id) {
  return (dispatch, getState) => {
    console.log('Loading device:', id);
    let r = client.devices.read(id);

    r.done((data, textStatus, xhrObject) => {
      dispatch(showDeviceResult(data));
    });
  }
}

const API_ROOT = 'http://localhost:8991';

export function loadDevice(id) {
  return {
    [CALL_API]: {
      endpoint: API_ROOT + Urls.device_detail(id),
      method: 'GET',
      types: [
        'DEVICE_DETAIL_REQUEST',
        'DEVICE_DETAIL_SUCCESS',
        'DEVICE_DETAIL_FAILURE'
      ]
    }
  };
}

export function loadDevices() {
  return (dispatch, getState) => {
    console.log('Loading devices.')
    let r = client.devices.read();

    r.done((data, textStatus, xhrObject) => {
      dispatch(showDevicesResult(data));
    });
  }
}

function shouldFetchDevices(state) {
  const devices = state.devices.rows
  if (!devices.length) {
    console.log('SHOULD FETCH DEVICES');
    return true
  }
  else {
    console.log('NO NEED TO FETCH DEVICES');
    return false
  }
}

export function fetchDevicesIfNeeded() {
  return (dispatch, getState) => {
    if (shouldFetchDevices(getState())) {
      return dispatch(loadDevices())
    }
  }
}

export function apiError(data) {
  return {
    type: 'API_ERROR',
    error: data.error.message
  };
}

/*
export function createDevice(data) {
  // FIXME(jathan): This shouldn't be hard-coded.
  data.site_id = 1;  // Inject site_id into payload.
  console.log('createDevice(data) =>', data);
  return {
    [CALL_API]: {
      endpoint: API_ROOT + Urls.device_list(),
      method: 'POST',
      headers: {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data),
      types: [
        'DEVICE_POST_REQUEST',
        'DEVICE_POST_SUCCESS',
        'DEVICE_POST_FAILURE',
      ]
    }
  };
}

export function _createDevice(data) {
  return (dispatch, getState) => {
    // FIXME(jathan): This shouldn't be hard-coded.
    data.site_id = 1;  // Inject site_id into payload.
    console.log('Creating device with data:', data);
    let r = client.devices.create(data);

    r.done((data, textStatus, xhrObject) => {
      // After device is created, take us to its page.
      dispatch(showDeviceResult(data));

      // FIXME(jathan) Nor should this be hard-coded
      dispatch(urlRedirect('/devices/' + data.id));
    })
    .fail((jqXHR, textStatus, errorThrown) => {
      let d = jqXHR;
      let msg = `Error (${d.status} - ${d.statusText}) while saving: ${d.responseText}`;
      console.log(msg);
      dispatch(apiError(d.responseJSON));
    });
  }
}
*/
