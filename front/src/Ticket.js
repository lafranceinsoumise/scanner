import { EVENT_LABELS, GENDER_LABELS } from "./labels";
import React from "react";

export function Ticket({ registration, validateScan, cancelScan }) {
  let style = {
    color: registration.category.color,
    backgroundColor: registration.category["background-color"],
  };

  return (
    <div id="registration" className="container registration" style={style}>
      {registration.canceled ? (
        <div className="alert alert-danger">
          Ce billet a été annulé ! Merci de renvoyer la personne à l'accueil.
        </div>
      ) : (
        ""
      )}
      {registration.meta.unpaid || registration.meta.status === "on-hold" ? (
        <div className="alert alert-danger">
          Cette personne n'a pas encore payé&nbsp;! Merci d'annuler et de la
          renvoyer à l'accueil.
        </div>
      ) : (
        ""
      )}
      {registration.events.find((event) => event.type === "entrance") && (
        <div className="alert alert-danger">
          Ce billet a déjà été scanné&nbsp;! Ne laissez entrer la personne
          qu'après vérification de son identité.
        </div>
      )}
      <h1 className="text-center">{registration.full_name}</h1>
      <h3>Catégorie&nbsp;: {registration.category.name}</h3>
      {registration.numero && <h3>#{registration.numero}</h3>}
      {["M", "F"].includes(GENDER_LABELS[registration.gender]) ? (
        <p>
          <b>Genre&nbsp;:</b> {registration.gender}
        </p>
      ) : (
        ""
      )}
      {!registration.canceled &&
      <button className="btn btn-block btn-success" onClick={validateScan}>
        OK
      </button>}
      <button className="btn btn-block btn-danger" onClick={cancelScan}>
        Annuler
      </button>

      {registration.events.length > 1 && (
        <>
          <h3>Historique</h3>
          <ul>
            {registration.events.slice(0, -1).map((event) => (
              <li key={event.time}>
                {EVENT_LABELS[event.type]} le{" "}
                {new Date(event.time).toLocaleString()} par {event.person}
                {event.point && ` (${event.point})`}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
