import React from "react";

export function Wait(props) {
  return (
    <div id="home">
      <div className="container">
        <p>Entrez vos noms et prénoms pour démarrer.</p>
        <form>
          <div className="form-group">
            <input
              className="form-control"
              type="text"
              value={props.value}
              onChange={props.onChange}
            />
          </div>
        </form>
        {props.value && props.value.length > 5 ? (
          <button className="btn btn-success btn-block" onClick={props.onClick}>
            Scanner
          </button>
        ) : (
          ""
        )}
      </div>
    </div>
  );
}
