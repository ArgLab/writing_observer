import {Component} from 'react';
import PropTypes from 'prop-types';

/**
 * A simple web socket interface to the Learning Observer
 *
 * We need to define an appropriate protocol here.
 * TODO remove anything to do with data scope
 */
export default class LOConnection extends Component {
    encode_query_string(obj) {
        // Creates a query string from an object
        // Example: {a:'b', c:'d'} ==> "a=b&c=d"

         const str = [];

         for (const prop in obj) {
             if (Object.prototype.hasOwnProperty.call(obj, prop)) {
                 str.push(
                     encodeURIComponent(prop) + "=" + encodeURIComponent(obj[prop])
                 );
             }
         }

      return str.join("&");
    }

    _init_client() {
        // Create a new client.
        let {url} = this.props;

        // Encode query string parameters
        const {data_scope} = this.props;
        const get_params = this.encode_query_string(data_scope);
        const params = (get_params ? `?${get_params}` : "")

        // Determine url
        const protocol = {"http:": "ws:", "https:": "wss:"}[window.location.protocol];
        url = url ? url : `${protocol}//${window.location.hostname}:${window.location.port}/wsapi/communication_protocol`;
        this.client = new WebSocket(url);
        // Listen for events.
        this.client.onopen = (e) => {
            // TODO: Add more properties here?
            this.props.setProps({
                state: {
                    // Mandatory props.
                    readyState: WebSocket.OPEN,
                    isTrusted: e.isTrusted,
                    timeStamp: e.timeStamp,
                    // Extra props.
                    origin: e.origin,
                }
            })
        }
        this.client.onmessage = (e) => {
            // TODO: Add more properties here?
            this.props.setProps({
                message: {
                    data: e.data,
                    isTrusted: e.isTrusted,
                    origin: e.origin,
                    timeStamp: e.timeStamp
                }
            })
        }
        this.client.onerror = (e) => {
            // TODO: Implement error handling.
            this.props.setProps({error: JSON.stringify(e)})
        }
        this.client.onclose = (e) => {
            // TODO: Add more properties here?
            this.props.setProps({
                state: {
                    // Mandatory props.
                    readyState: WebSocket.CLOSED,
                    isTrusted: e.isTrusted,
                    timeStamp: e.timeStamp,
                    // Extra props.
                    code: e.code,
                    reason: e.reason,
                    wasClean: e.wasClean,
                }
            })
        }
    }

    componentDidMount() {
        this._init_client()
    }

    componentDidUpdate(prevProps) {
        const {send, data_scope} = this.props;
        // Send messages.
        if (send && send !== prevProps.send) {
            if (this.props.state.readyState === WebSocket.OPEN) {
                this.client.send(send)
            }
        }
        // Close and re-open the websocket with new data
        if (JSON.stringify(data_scope) !== JSON.stringify(prevProps.data_scope)) {
            this.client.close();
            this._init_client();
        }
    }

    componentWillUnmount() {
        // Clean up (close the connection).
        this.client.close();
    }

    render() {
        return (null);
    }

}

LOConnection.defaultProps = {
    state: {readyState: WebSocket.CONNECTING}
}

LOConnection.propTypes = {

    /**
     * This websocket state (in the readyState prop) and associated information.
     */
    state: PropTypes.oneOfType([PropTypes.object, PropTypes.string]),

    /**
     * When messages are received, this property is updated with the message content.
     */
    message: PropTypes.oneOfType([PropTypes.object, PropTypes.string]),

    /**
     * This property is set with the content of the onerror event.
     */
    error: PropTypes.oneOfType([PropTypes.object, PropTypes.string]),

    /**
     * When this property is set, a message is sent with its content.
     */
    send: PropTypes.oneOfType([PropTypes.object, PropTypes.string]),

    /**
     * The websocket endpoint (e.g. wss://echo.websocket.org).
     */
    url: PropTypes.string,

    /**
     * Supported websocket key (optional).
     */
    data_scope: PropTypes.object,

    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * Dash-assigned callback that should be called to report property changes
     * to Dash, to make them available for callbacks.
     */
    setProps: PropTypes.func

}
