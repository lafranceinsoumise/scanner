import React, { useState } from "react";
import Scanner from "./Scanner";
import "./App.css";
import config from "./config";
import { Wait } from "./Wait";
import { EVENT_LABELS } from "./labels";
import { Ticket } from "./Ticket";

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
        <Ticket
          style={style}
          registration={registration}
          callbackfn={(event) => (
            <li key={event.time}>
              {EVENT_LABELS[event.type]} le{" "}
              {new Date(event.time).toLocaleString()} par {event.person}
            </li>
          )}
          predicate={(event) => event.type === "entrance"}
          onClick={validateScan}
          onClick1={cancelScan}
        />
      );
    case "scan":
      return <Scanner clickBack={wait} scan={scan} />;
    case "wait":
    default:
      return (
        <Wait
          value={user}
          onChange={personFieldChange}
          onClick={startScanning}
        />
      );
  }
};

export default App;
