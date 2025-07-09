import { EVENT_LABELS, GENDER_LABELS } from "./labels";
import React from "react";

const ALERT_STYLE = {
  fontWeight: "600",
  fontSize: "2.4rem",
  lineHeight: "1.4",
  textAlign: "center",
  fontFamily: "Arial, sans-serif"
};

const Alert = ({ children }) => (
  <div style={ALERT_STYLE} className="alert alert-danger">
    {children}
  </div>
);

// Fonction utilitaire pour savoir si une personne est mineure
function isMinor(dateOfBirthStr) {
  if (!dateOfBirthStr) return false;

  const birthDate = new Date(dateOfBirthStr);
  const today = new Date();

  let age = today.getFullYear() - birthDate.getFullYear();
  const m = today.getMonth() - birthDate.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }

  return age < 18;
}

export function Ticket({ registration, validateScan, cancelScan }) {
  let style = {
    color: registration.category.color,
    backgroundColor: registration.category["background-color"],
    position: "absolute",
    width: "100%",
    minHeight: "100%",
  };

  return (
    <div id="registration" className="container registration" style={style}>
      {registration.canceled && (
        <Alert>
          Ce billet a été annulé ! Merci de renvoyer la personne à l'accueil.
        </Alert>
      )}

      {(registration.meta.unpaid || registration.meta.status === "on-hold") && (
        <Alert>
          Cette personne n'a pas encore payé&nbsp;! Merci d'annuler et de la
          renvoyer à l'accueil.
        </Alert>
      )}

      {registration.events.find((event) => event.type === "entrance") && (
        <Alert>
          Ce billet a déjà été scanné&nbsp;! Ne laissez entrer la personne
          qu'après vérification de son identité.
        </Alert>
      )}

      {isMinor(registration.meta.date_of_birth) && (
        <Alert>
          Cette personne est mineure&nbsp;! Merci d'annuler et de la
          renvoyer à l'accueil.
        </Alert>
      )}

      <h1 className="text-center">{registration.full_name}</h1>
      <h3>Catégorie&nbsp;: {registration.category.name}</h3>
      {registration.numero && <h3>#{registration.numero}</h3>}
      {["M", "F"].includes(GENDER_LABELS[registration.gender]) ? (
        <p>
          <b>Genre&nbsp;:</b> {registration.gender}
        </p>
      ) : null}

      {!registration.canceled && (
        <button className="btn btn-block btn-success" onClick={validateScan}>
          OK
        </button>
      )}
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
