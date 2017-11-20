import React, { Component } from 'react';
import Scanner from './Scanner';
import './App.css';

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {action: 'wait'};
  }

  startScanning() {
    this.setState({action: 'scan'});
  }

  wait() {
    this.setState({action: 'wait'});
  }

  render() {
    switch (this.state.action) {
      case 'scan':
        return (
          <Scanner clickBack={this.wait.bind(this)}/>
        );
      case 'wait':
      default:
        return (
          <div id="home">
            <button className="btn btn-primary btn-block" onClick={this.startScanning.bind(this)}>Scanner</button>
          </div>
        )
    }
  }
}

export default App;
