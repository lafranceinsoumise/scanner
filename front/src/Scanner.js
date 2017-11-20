import React, { Component } from 'react';
import Instascan from 'instascan';

import config from './config';

class Scanner extends Component {
  constructor(props) {
    super(props);
    this.clickBack = props.clickBack;
    this.state = {}
  }

  async componentDidMount() {
    this.scanner = new Instascan.Scanner({
      video: document.getElementById('preview'),
      mirror: false
    });

    this.cameras = await Instascan.Camera.getCameras();
    if (this.cameras.length > 0) {
      this.camera = 0;
      this.scanner.start(this.cameras[0]);
    } else {
      console.error('No cameras found.');
    }
    this.scanner.addListener('scan', async (content) => {
      this.setState({loading: true});

      try {
        let response = await fetch(config.host + '/api/' + content);

        if (response.ok) {
          alert(await response.text());
        }
      } catch (e) {
        alert(e);
      } finally {
        this.setState({lading: false});
      }
    });
  }

  changeCamera() {
    this.camera++;
    this.scanner.start(this.cameras[this.camera % this.cameras.length]);
  }

  render() {
    return (
      <div id="scanner">
        <video id="preview"></video>
        {this.state.loading ? <p>'Chargement...'</p> : ''}
        <button id="changeButton" className="btn btn-success" onClick={this.changeCamera.bind(this)}>Changer la camera</button>
        <button id="changeButton" className="btn btn-danger" onClick={this.clickBack}>Retour</button>
      </div>
    );
  }
}

export default Scanner;
