import React from 'react'
import {EventableComponent, AppEvents} from 'react-at-rest'
import DeviceList from './components/device_list'

// EventableComponent provides event-handling methods such as @listenTo and @stopListening
class App extends EventableComponent {

  componentDidMount() {
    // Setup some global error-handling
    this.listenTo(AppEvents, 'api.exception', (error) => {
      console.error(error);
    });
  }

  render() {
    return (
      <div className="container">
        <h1>Devices</h1>
        <DeviceList />
      </div>
    );
  }

}

/*
class App extends React.Component {
  render() {
    return (
      <div className="container">
        <h1>Devices</h1>
        <pre>Hi!</pre>
      </div>
    );
  }

}
*/

module.exports = App;
