import React from "react";

export function Container(props) {
  return (
    <div id="home">
      <div className="container">{props.children}</div>
    </div>
  );
}
