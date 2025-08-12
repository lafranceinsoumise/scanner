import React, { useState } from "react";
import config from "./config";
import useSWR from "swr";
import { Container } from "./Container";
import { jsonFetch } from "./utils";

export function Start({ user, setUser, setPoint, setEvent}) {
  const { data: events, error } = useSWR(
    `${config.host}/api/events/`,
    jsonFetch
  );
  const [name, setName] = useState(user || localStorage.getItem("lastName"));

  if (!user) {
    return (
      <Container>
        <p>Entrez vos noms et prénoms pour démarrer</p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (name && name.length >= 6) {
              setUser(name);
              localStorage.setItem("lastName", name);
            }
          }}
        >
          <div className="form-group">
            <input
              autoFocus
              className="form-control input-lg"
              type="text"
              value={name || ""}
              onChange={(event) => setName(event.target.value)}
            />
          </div>
          <button
            type="submit"
            className="btn btn-success btn-block"
            disabled={!name || name.length < 6}
          >
            Démarrer
          </button>
        </form>
      </Container>
    );
  }

  if (user && !events) {
    return <Container>Chargement...</Container>;
  }

  if (user && error) {
    return <Container>Erreur</Container>;
  }

  function clickOnEvent(event) {
    setPoint(event.scan_points[0].id);
    setUser(name);
    setEvent(event);
  }

  // choix event et selection du point 0 si pas d'autres points
  if (events && events.length > 1) {
    return (
      <Container>
        <p>Choisissez l'événement auquel vous participez</p>
        <div className="list-group">
          {events.map((event) => (
            <button
              key={event.name}
              className="list-group-item list-group-item-action"
              onClick={() => clickOnEvent(event)}
            >
              {event.name}
            </button>
          ))}
        </div>
      </Container>
    );
  }

  // si un seul event, on le sélectionne automatiquement
  if (events && events.length === 1 && events[0].scan_points.length > 1) {
    return (
      <Container>
        <p>Choisissez le point de scan</p>
        <div className="list-group">
          {events[0].scan_points.map((point) => (
            <button
              key={point.id}
              className="list-group-item list-group-item-action"
              onClick={() => {
                setPoint(point.id);
                setUser(name);
              }}
            >
              {point.name}
            </button>
          ))}
        </div>
      </Container>
    );
  }

  // pas d'event, juste point
  if (events && events.length === 1) {
    setPoint(events[0].scan_points[0].id);
  }

  return null;
}
