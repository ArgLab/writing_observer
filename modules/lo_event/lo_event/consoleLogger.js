function consoleLog (event) {
  console.log(event);
}

export function consoleLogger () {
  /*
  Log to browser JavaScript console
  */
  consoleLog.init = function () { console.log('Initializing console logger!'); };
  consoleLog.setField = function (metadata) { console.log('setField:', metadata); };
  consoleLog.lo_name = 'Console Logger';

  return consoleLog;
}
