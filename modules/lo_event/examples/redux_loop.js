import { createRoot } from "react-dom/client";
import * as lo_event from '../lo_event/lo_event';
import * as reduxLogger from '../lo_event/reduxLogger.js';
import { consoleLogger } from '../lo_event/consoleLogger.js';
import * as debug from '../lo_event/debugLog.js';
import { init } from '../lo_event/lo_assess/lo_assess.js';
import { ActionButton, PopupAction, ConsoleAction } from '../lo_event/lo_assess/components/components.jsx';

init();

lo_event.go();

export function App() {
  return (
    <>
      <h1>Hello world!!</h1>
      <p> This demos how we can build actions with our API. Pressing the button will cause an alert and a console.log </p>
      <ActionButton>
        Test!
        <PopupAction>
          I am a little action, short and stout!
        </PopupAction>
        <ConsoleAction>
          I am a bit of text!
        </ConsoleAction>
      </ActionButton>
    </>
  );
}

const container = document.getElementById("app");
const root = createRoot(container);
root.render(<App />);
