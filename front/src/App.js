import React, { Component } from 'react';
import Scanner from './Scanner';
import './App.css';
import config from './config';

const TYPE_LABELS = {
  invite: 'Invité⋅e',
  participant: 'Participant⋅e',
  volontaire: 'Volontaire',
  volontaire_referent: 'Volontaire référent⋅e',
  village: 'Village',
  so: 'Accueil et SO',
}

const EVENT_LABELS = {
  entrance: 'Entrée validée',
  scan: 'Code scanné',
  cancel: 'Scan annulé'
}

const GENDER_LABELS = {
  H: 'Homme',
  F: 'Femme',
}

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {action: 'wait'};
  }

  // Start and stop scanning

  personFieldChange(event) {
    this.setState({scanningPerson: event.target.value});
  }

  startScanning() {
    this.setState({action: 'scan'});
  }

  wait() {
    this.setState({action: 'wait'});
  }

  // Take action with scanners

  successfulScan(registration, code) {
    this.setState({action: 'displayRegistration', registration, code});
  }

  async scan(content) {
    navigator.vibrate(200);
    let response;

    response = await fetch(`${config.host}/api/${content}/?person=${encodeURIComponent(this.state.scanningPerson)}`);

    if (response.ok) {
      this.successfulScan(await response.json(), content);
    }
  }

  async validateScan() {
    let form = new FormData();
    form.append('type', 'entrance');

    await fetch(`${config.host}/api/${this.state.code}/?person=${encodeURIComponent(this.state.scanningPerson)}`, {
      method: 'POST',
      body: form,
    });

    this.setState({action: 'scan'});
  }

  async cancelScan() {
    let form = new FormData();
    form.append('type', 'cancel');

    await fetch(`${config.host}/api/${this.state.code}/?person=${encodeURIComponent(this.state.scanningPerson)}`, {
      method: 'POST',
      body: form,
    });

    this.setState({action: 'scan'});
  }

  render() {
    switch (this.state.action) {
      case 'displayRegistration':
        let registration = this.state.registration;
        return (
          <div id="registration" className={"container registration-" + registration.type}>
            <h1 className="text-center">{registration.full_name}</h1>
            <h3>Rôle&nbsp;: {TYPE_LABELS[registration.type]}</h3>
            <h3>#{registration.numero}</h3>
            {['M', 'F'].includes(GENDER_LABELS[registration.gender]) ? (
              <p><b>Genre&nbsp;:</b> {registration.gender}</p>
            ) : ''}
            {registration.events.length > 1 && <p><b>Historique&nbsp;:</b></p>}
            <ul>{registration.events.slice(0, -1).map((event) => (
                <li key={event.time}>{EVENT_LABELS[event.type]} le {new Date(event.time).toLocaleString()}</li>
            ))}</ul>
            {registration.events.find(event => event.type === 'entrance') ? (
              <div className="alert alert-danger">
                Ce billet a déjà été scanné&nbsp;! Ne laissez entrer la personne
                qu'après vérification de son identité.
              </div>
            ) : ''}
            <button className="btn btn-block btn-success" onClick={this.validateScan.bind(this)}>OK</button>
            <button className="btn btn-block btn-danger" onClick={this.cancelScan.bind(this)}>Annuler</button>
          </div>
        );
      case 'scan':
        return (
          <Scanner clickBack={this.wait.bind(this)} scan={this.scan.bind(this)}/>
        );
      case 'wait':
      default:
        return (
          <div id="home">
            <div class="container">
              <p>Entrez vos noms et prénoms pour démarrer.</p>
              <form>
                <div class="form-group">
                  <input className="form-control" type="text" value={this.state.scanningPerson} onChange={this.personFieldChange.bind(this)} />
                </div>
              </form>
              {this.state.scanningPerson && this.state.scanningPerson.length > 5 ? (
                <button className="btn btn-success btn-block" onClick={this.startScanning.bind(this)}>Scanner</button>
              ): ''}
            </div>
          </div>
        )
    }
  }
}

export default App;
