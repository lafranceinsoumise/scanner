import React, { useState } from "react";
import config from "./config";
import useSWR from "swr";
import { Container } from "./Container";
import { jsonFetch } from "./utils";

export function Start(props) {
  const { data: events, error } = useSWR(
    `${config.host}/api/events`,
    jsonFetch
  );
  const [name, setName] = useState("");
  const [step, setStep] = useState(0);

  if (step === 0) {
    return (
      <Container>
        <p>Entrez vos noms et prénoms pour démarrer</p>
        <form>
          <div className="form-group">
            <input
              className="form-control input-lg"
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </div>
        </form>
        {
          <button
            className="btn btn-success btn-block"
            onClick={() => {
              props.setName(name);
              setStep(1);
            }}
            disabled={name.length < 6}
          >
            Démarrer
          </button>
        }
      </Container>
    );
  }

  if (step === 1 && !events) {
    return <Container>Chargement...</Container>;
  }

  if (step === 1 && error) {
    return <Container>Erreur</Container>;
  }

  if (step === 1 && events) {
    return (
      <Container>
        <h1>Choisissez le point de contrôle</h1>
        <>
          {events[0].scan_points.map(({ id, name }) => (
            <button
              key={id}
              className="btn btn-default btn-block"
              onClick={() => props.setPoint(id)}
            >
              {name}
            </button>
          ))}
        </>
      </Container>
    );
  }
}
