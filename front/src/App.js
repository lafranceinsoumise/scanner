import React, { useState } from "react";
import Scanner from "./Scanner";
import "./App.css";
import config from "./config";

const EVENT_LABELS = {
  entrance: "Entrée validée",
  scan: "Code scanné",
  cancel: "Scan annulé",
};

const GENDER_LABELS = {
  H: "Homme",
  M: "Homme",
  F: "Femme",
};

const App = (props) => {
  const [action, setAction] = useState("wait");
  const [lastScan, setLastScan] = useState(null);
  const [user, setUser] = useState(null);

  // Start and stop scanning

  function personFieldChange(event) {
    setUser(event.target.value);
  }

  function startScanning() {
    setAction("scan");
  }

  function wait() {
    setAction("wait");
  }

  // Take action with scanners

  function successfulScan(registration, code) {
    setAction("displayRegistration");
    setLastScan({ registration, code });
  }

  let scan = async (content) => {
    navigator.vibrate(200);
    let response;

    response = await fetch(
      `${config.host}/code/${content}/?person=${encodeURIComponent(user)}`
    );

    if (response.ok) {
      return successfulScan(await response.json(), content);
    }

    if (response.status === 404) {
      throw new Error("Not Found");
    }
  };

  let validateScan = async () => {
    let form = new FormData();
    form.append("type", "entrance");

    await fetch(
      `${config.host}/code/${lastScan.code}/?person=${encodeURIComponent(
        user
      )}`,
      {
        method: "POST",
        body: form,
      }
    );

    setAction("scan");
  };

  let cancelScan = async () => {
    let form = new FormData();
    form.append("type", "cancel");

    await fetch(
      `${config.host}/code/${lastScan.code}/?person=${encodeURIComponent(
        user
      )}`,
      {
        method: "POST",
        body: form,
      }
    );

    setAction("scan");
  };

  switch (action) {
    case "displayRegistration":
      let registration = lastScan.registration;
      let style = {
        color: registration.category.color,
        "background-color": registration.category["background-color"],
      };

      return (
        <div id="registration" className="container registration" style={style}>
          {registration.meta.unpaid ||
          registration.meta.status === "on-hold" ? (
            <div className="alert alert-danger">
              Cette personne n'a pas encore payé&nbsp;! Merci d'annuler et de la
              renvoyer à l'accueil.
            </div>
          ) : (
            ""
          )}
          <h1 className="text-center">{registration.full_name}</h1>
          <h3>Catégorie&nbsp;: {registration.category.name}</h3>
          <h3>#{registration.numero}</h3>
          {["M", "F"].includes(GENDER_LABELS[registration.gender]) ? (
            <p>
              <b>Genre&nbsp;:</b> {registration.gender}
            </p>
          ) : (
            ""
          )}
          {registration.events.length > 1 && (
            <p>
              <b>Historique&nbsp;:</b>
            </p>
          )}
          <ul>
            {registration.events.slice(0, -1).map((event) => (
              <li key={event.time}>
                {EVENT_LABELS[event.type]} le{" "}
                {new Date(event.time).toLocaleString()} par {event.person}
              </li>
            ))}
          </ul>
          {registration.events.find((event) => event.type === "entrance") ? (
            <div className="alert alert-danger">
              Ce billet a déjà été scanné&nbsp;! Ne laissez entrer la personne
              qu'après vérification de son identité.
            </div>
          ) : (
            ""
          )}
          <button className="btn btn-block btn-success" onClick={validateScan}>
            OK
          </button>
          <button className="btn btn-block btn-danger" onClick={cancelScan}>
            Annuler
          </button>
        </div>
      );
    case "scan":
      return <Scanner clickBack={wait} scan={scan} />;
    case "wait":
    default:
      return (
        <div id="home">
          <div className="container">
            <p>Entrez vos noms et prénoms pour démarrer.</p>
            <form>
              <div className="form-group">
                <input
                  className="form-control"
                  type="text"
                  value={user}
                  onChange={personFieldChange}
                />
              </div>
            </form>
            {user && user.length > 5 ? (
              <button
                className="btn btn-success btn-block"
                onClick={startScanning}
              >
                Scanner
              </button>
            ) : (
              ""
            )}
          </div>
        </div>
      );
  }
};

export default App;
