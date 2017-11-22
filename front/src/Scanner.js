import React, { Component } from 'react';

import config from './config';

class Scanner extends Component {
  constructor(props) {
    super(props);
    this.clickBack = props.clickBack;
    this.successfulScan = props.successfulScan;
    this.state = {}

    this.activeCamera = 0;
  }

  async componentDidMount() {
    this.scanner = this.scanner || new window.Instascan.Scanner({
      video: document.getElementById('preview'),
      mirror: false
    });
    this.cameras = await window.Instascan.Camera.getCameras();
    if (this.cameras.length > 0) {
      await this.scanner.start(this.cameras[this.activeCamera]);
    } else {
      console.error('No cameras found.');
    }

    this.scanner.addListener('scan', async (content) => {
      navigator.vibrate(200);
      this.setState({loading: true});

      let response;
      try {
        response = await fetch(config.host + '/api/' + content + '/');
        await this.scanner.stop();

        if (response.ok) {
          this.successfulScan(await response.json(), content);
        }
      } catch (e) {
        this.error();
      }
    });
  }

  error() {
    this.setState({loading: false});
  }

  changeCamera() {
    this.activeCamera++;
    this.scanner.start(this.cameras[this.camera % this.cameras.length]);
  }

  render() {
    return (
      <div id="scanner">
        <video id="preview"></video>
        {this.state.loading ? (
          <div className="container">
            <div className="alert alert-info">'Chargement...'</div>
          </div>
        ) : ''}
        <button id="changeButton" className="btn btn-success" onClick={this.changeCamera.bind(this)}>Changer la camera</button>
        <button id="changeButton" className="btn btn-danger" onClick={this.clickBack}>Pause</button>
      </div>
    );
  }
}

export default Scanner;
