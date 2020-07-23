import React, { Component } from "react";

class Scanner extends Component {
  constructor(props) {
    super(props);
    this.scan = props.scan;
    this.state = { pause: false };

    this.activeCamera = localStorage.getItem("preferedCamera") || 0;
  }

  async startCamera() {
    if (!this.scanner) {
      this.scanner = new window.Instascan.Scanner({
        video: document.getElementById("preview"),
        mirror: false,
      });

      this.cameras = await window.Instascan.Camera.getCameras();

      this.scanner.addListener("scan", async (content) => {
        this.setState({ loading: true });
        try {
          await this.scan(content);
        } catch (err) {
          if (err.message === "Not Found") {
            return this.error("Billet inconnu.");
          }

          return this.error();
        }

        this.setState({ loading: false });
      });
    }

    if (this.cameras.length > 0) {
      await this.scanner.start(
        this.cameras[this.activeCamera % this.cameras.length]
      );
    } else {
      console.error("No cameras found.");
    }
  }

  async stopCamera() {
    localStorage.setItem(
      "preferedCamera",
      this.activeCamera % this.cameras.length
    );
    await this.scanner.stop();
  }

  async componentDidMount() {
    return await this.startCamera();
  }

  async componentWillUnmount() {
    return await this.stopCamera();
  }

  error(message) {
    this.setState({
      loading: false,
      error: message || "Impossible de lire le billet.",
    });
    setTimeout(() => {
      this.setState({ error: false });
    }, 3000);
  }

  changeCamera() {
    this.activeCamera++;
    this.scanner.start(this.cameras[this.activeCamera % this.cameras.length]);
  }

  render() {
    return (
      <div id="scanner">
        <video id="preview" />
        {this.state.loading ? (
          <div className="container">
            <div className="alert alert-info">'Chargement...'</div>
          </div>
        ) : (
          ""
        )}
        {this.state.error ? (
          <div className="container">
            <div className="alert alert-danger">{this.state.error}</div>
          </div>
        ) : (
          ""
        )}
        <button
          id="changeButton"
          className="btn btn-success"
          onClick={this.changeCamera.bind(this)}
        >
          Changer la camera
        </button>
        <button
          id="changeButton"
          className="btn btn-danger"
          onClick={() => {
            this.setState({ pause: !this.state.pause });
            this.state.pause ? this.startCamera() : this.stopCamera();
          }}
        >
          {this.state.pause
            ? "Relancer la caméra"
            : "Mettre en pause la caméra"}
        </button>
      </div>
    );
  }
}

export default Scanner;
