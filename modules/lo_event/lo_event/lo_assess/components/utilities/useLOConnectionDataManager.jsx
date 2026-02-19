/**
 * useLOConnectionDataManager handles storing and processing incoming
 * messages from the communication protocol websocket connection.
 * This hook wraps the useLOConnection hook to fetch updates.
 * The communication protocol sends batches of updates to apply
 * to a clientside data object.
 *
 * When the internal data is updated, we call the `onDataUpdate`
 * parameter so parents can update accordingly.
 * 
 * useLOConnectionDataManager exposes the following items:
 * - `data`: current overall data received from websocket messages
 * - `errors`: information about any errors received
 * - `connection`: all returned items from useLOConnection
 *
 * Usage:
 * ```js
  const { data, errors, sendMessage } = useLOConnectionDataManager({ url, dataScope });

  return (
    <div>
      <div>
        <h2>User Data</h2>
        {Object.keys(data).length > 0 ? (
          <pre>{JSON.stringify(data, null, 2)}</pre>
        ) : (
          <p>No user data available.</p>
        )}
      </div>
      {Object.keys(errors).length > 0 && (
        <div style={{ color: 'red' }}>
          <h2>Errors</h2>
          <pre>{JSON.stringify(errors, null, 2)}</pre>
        </div>
      )}
    </div>
  );
 * ```
 */
import { useReducer, useEffect } from 'react';
import { useLOConnection } from './useLOConnection'; // Assuming LOConnection is renamed to useLOConnection

// Reducer function for managing state updates
const dataReducer = (state, action) => {
  switch (action.type) {
    case 'update': {
      const { path, value } = action.payload;
      const pathKeys = path.split('.');

      // Create a new `data` object with the updated value at the correct path
      const newData = { ...state.data };
      let current = newData; // Start at the top-level copy
      for (let i = 0; i < pathKeys.length - 1; i++) {
        const key = pathKeys[i];
        if (!(key in current)) {
          current[key] = {}; // Create path if it doesn't exist
        } else {
          current[key] = { ...current[key] }; // Copy the existing nested object
        }
        current = current[key];
      }

      const finalKey = pathKeys[pathKeys.length - 1];
      // TODO this doesn't handle a deep merge
      current[finalKey] = {
        ...current[finalKey], // Existing data
        ...value, // New data (overwrites where necessary)
      };

      return {
        ...state,
        data: newData,
      };
    }
    case 'error': {
      const { path, value } = action.payload;
      return {
        ...state,
        errors: {
          ...state.errors,
          [path]: value,
        },
      };
    }
    case 'clearError': {
      const { path } = action.payload;
      const newErrors = { ...state.errors };
      delete newErrors[path];
      return {
        ...state,
        errors: newErrors,
      };
    }
    default:
      console.warn(`Unhandled action type: ${action.type}`);
      return state;
  }
};

// Initial state for the reducer
const initialState = {
  data: {},
  errors: {},
};

export const useLOConnectionDataManager = ({ url, dataScope }) => {
  const { message, ...connection } = useLOConnection({ url, dataScope });
  const [state, dispatch] = useReducer(dataReducer, initialState);

  useEffect(() => {
    if (message) {
      try {
        const messages = JSON.parse(message);

        messages.forEach((msg) => {
          if ('error' in msg.value) {
            dispatch({ type: 'error', payload: { path: msg.path, value: msg.value } });
          } else {
            dispatch({ type: 'clearError', payload: { path: msg.path } });
            dispatch({ type: msg.op, payload: { path: msg.path, value: msg.value } });
          }
        });
      } catch (e) {
        console.error('Failed to parse incoming message:', e);
      }
    }
  }, [message]);

  return {
    connection,
    data: state.data,
    errors: state.errors,
  };
};
