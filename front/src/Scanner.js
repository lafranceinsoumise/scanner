import React, { Component } from 'react';

class Scanner extends Component {
  constructor(props) {
    super(props);
    this.clickBack = props.clickBack;
    this.scan = props.scan;
    this.state = {}

    this.activeCamera = localStorage.getItem('preferedCamera') || 0;
  }

  async componentDidMount() {
    if (!this.scanner) {
      this.scanner = new window.Instascan.Scanner({
        video: document.getElementById('preview'),
        mirror: false
      });

      this.cameras = await window.Instascan.Camera.getCameras();

      this.scanner.addListener('scan', async (content) => {
        this.setState({loading: true});
        try {
          await this.scan(content);
        } catch (err) {
          this.error();
        }
      });
    }

    if (this.cameras.length > 0) {
      await this.scanner.start(this.cameras[this.activeCamera % this.cameras.length]);
    } else {
      console.error('No cameras found.');
    }
  }

  async componentWillUnmount () {
      localStorage.setItem('preferedCamera', this.activeCamera % this.cameras.length)
      await this.scanner.stop();
  }

  error() {
    this.setState({loading: false, error: 'Impossible de lire le billet.'});
    setTimeout(() => {
      this.setState({error: false});
    }, 3000);
  }

  changeCamera() {
    this.activeCamera++;
    this.scanner.start(this.cameras[this.activeCamera % this.cameras.length]);
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
        {this.state.error ? (
          <div className="container">
            <div className="alert alert-danger">{this.state.error}</div>
          </div>
        ) : ''}
        <button id="changeButton" className="btn btn-success" onClick={this.changeCamera.bind(this)}>Changer la camera</button>
        <button id="changeButton" className="btn btn-danger" onClick={this.clickBack}>Pause</button>
      </div>
    );
  }
}

export default Scanner;
