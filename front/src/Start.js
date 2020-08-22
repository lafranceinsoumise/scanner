import React, { useState } from "react";
import config from "./config";
import useSWR from "swr";
import { Container } from "./Container";
import { jsonFetch } from "./utils";

export function Start({ user, setUser, setPoint }) {
  const { data: events, error } = useSWR(
    `${config.host}/api/events`,
    jsonFetch
  );
  const [name, setName] = useState(user);

  if (!user) {
    return (
      <Container>
        <p>Entrez vos noms et prénoms pour démarrer</p>
        <form>
          <div className="form-group">
            <input
              className="form-control input-lg"
              type="text"
              value={name || ""}
              onChange={(event) => setName(event.target.value)}
            />
          </div>
        </form>
        {
          <button
            className="btn btn-success btn-block"
            onClick={() => {
              setUser(name);
              setName(name);
            }}
            disabled={!name || name.length < 6}
          >
            Démarrer
          </button>
        }
      </Container>
    );
  }

  if (user && !events) {
    return <Container>Chargement...</Container>;
  }

  if (user && error) {
    return <Container>Erreur</Container>;
  }

  if (user && events) {
    return (
      <Container>
        <h1>Choisissez le point de contrôle</h1>
        <>
          {events[0].scan_points.map(({ id, name }) => (
            <button
              key={id}
              className="btn btn-default btn-block"
              onClick={() => setPoint(id)}
            >
              {name}
            </button>
          ))}
        </>
      </Container>
    );
  }
}
