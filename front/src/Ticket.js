import { GENDER_LABELS } from "./labels";
import React from "react";

export function Ticket(props) {
  return (
    <div
      id="registration"
      className="container registration"
      style={props.style}
    >
      {props.registration.meta.unpaid ||
      props.registration.meta.status === "on-hold" ? (
        <div className="alert alert-danger">
          Cette personne n'a pas encore payé&nbsp;! Merci d'annuler et de la
          renvoyer à l'accueil.
        </div>
      ) : (
        ""
      )}
      <h1 className="text-center">{props.registration.full_name}</h1>
      <h3>Catégorie&nbsp;: {props.registration.category.name}</h3>
      <h3>#{props.registration.numero}</h3>
      {["M", "F"].includes(GENDER_LABELS[props.registration.gender]) ? (
        <p>
          <b>Genre&nbsp;:</b> {props.registration.gender}
        </p>
      ) : (
        ""
      )}
      {props.registration.events.length > 1 && (
        <p>
          <b>Historique&nbsp;:</b>
        </p>
      )}
      <ul>{props.registration.events.slice(0, -1).map(props.callbackfn)}</ul>
      {props.registration.events.find(props.predicate) ? (
        <div className="alert alert-danger">
          Ce billet a déjà été scanné&nbsp;! Ne laissez entrer la personne
          qu'après vérification de son identité.
        </div>
      ) : (
        ""
      )}
      <button className="btn btn-block btn-success" onClick={props.onClick}>
        OK
      </button>
      <button className="btn btn-block btn-danger" onClick={props.onClick1}>
        Annuler
      </button>
    </div>
  );
}
