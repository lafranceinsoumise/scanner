import React, { useCallback, useEffect, useRef, useState } from "react";
import cursorFill from "bootstrap-icons/icons/cursor-fill.svg";
import person from "bootstrap-icons/icons/person.svg";
import people from "bootstrap-icons/icons/people.svg";
import X from "bootstrap-icons/icons/x.svg";
import useSWR, { mutate } from "swr";
import config from "./config";
import { jsonFetch, postForm } from "./utils";

function Scanner({ scan, setPoint, user, point }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [pause, setPause] = useState(false);
  const scanner = useRef(null);
  const cameras = useRef(null);
  const activeCamera = useRef(null);

  const { data: events } = useSWR(`${config.host}/api/events`, jsonFetch);

  const displayError = useCallback((message) => {
    setLoading(false);
    setError(message || "Impossible de lire le billet.");

    setTimeout(() => {
      setError(false);
    }, 3000);
  }, []);

  const startCamera = useCallback(async () => {
    if (!scanner.current) {
      scanner.current = new window.Instascan.Scanner({
        video: document.getElementById("preview"),
        mirror: false,
      });

      cameras.current = await window.Instascan.Camera.getCameras();

      scanner.current.addListener("scan", async (content) => {
        setLoading(true);

        try {
          await scan(content);
        } catch (err) {
          if (err.message === "Not Found") {
            return displayError("Billet inconnu.");
          }

          return displayError();
        }

        setLoading(false);
      });
    }

    if (cameras.current.length > 0) {
      let savedCam = localStorage.getItem("preferedCamera");

      if (Number.isInteger(savedCam)) {
        activeCamera.current = savedCam;
      }
      await scanner.current.start(
        cameras.current[activeCamera.current % cameras.current.length]
      );
    } else {
      console.error("No cameras found.");
    }
  }, [displayError, scan]);

  const changeCamera = useCallback(async () => {
    activeCamera.current++;
    activeCamera.current %= cameras.current.length;
    await scanner.current.start(cameras.current[activeCamera.current]);
  }, [activeCamera, scanner]);

  const stopCamera = useCallback(async () => {
    localStorage.setItem("preferedCamera", activeCamera.current);
    await scanner.current.stop();
  }, [scanner]);

  useEffect(() => {
    startCamera();
    return function cleanup() {
      stopCamera();
    };
  }, [startCamera, stopCamera]);

  let eventName =
    events && events[0].scan_points.find((e) => e.id === point).name;
  let eventCount =
    events && events[0].scan_points.find((e) => e.id === point).count;

  return (
    <div id="scanner">
      <div
        style={{ backgroundColor: "#fff", width: "100%" }}
        className="container-fluid"
      >
        <div className="row" style={{ marginTop: "20px" }}>
          <div className="col-xs-6">
            <p>
              <img src={person} alt={"Utilisateur⋅ice"} /> {user}
            </p>
            <p>
              <img src={cursorFill} alt={"Point de contrôle"} /> {eventName}{" "}
              <img
                onClick={() => setPoint(null)}
                className="pull-right"
                src={X}
                alt={"Changer le lieu"}
              />
            </p>
          </div>
          <div className="col-xs-6">
            {eventCount !== null && (
              <>
                <p>
                  <img src={people} alt={"Compteur"} /> {eventCount}
                </p>
                <button
                  className="btn btn-info btn-sm"
                  onClick={async () => {
                    await postForm(`${config.host}/reset/`, {
                      point,
                    });
                    await mutate(`${config.host}/api/events`);
                  }}
                >
                  Remettre à zéro
                </button>
              </>
            )}
          </div>
        </div>
      </div>
      <video id="preview" />
      <div>
        {loading && (
          <div className="container">
            <div className="alert alert-info">'Chargement...'</div>
          </div>
        )}
        {error && (
          <div className="container">
            <div className="alert alert-danger">{error}</div>
          </div>
        )}
        <button
          id="changeButton"
          className="btn btn-lg btn-success btn-block"
          onClick={changeCamera}
        >
          Changer la camera
        </button>
        <button
          id="changeButton"
          className="btn btn-lg btn-danger btn-block"
          onClick={() => {
            setPause(!pause);
            pause ? startCamera() : stopCamera();
          }}
        >
          {pause ? "Relancer la caméra" : "Mettre en pause la caméra"}
        </button>
      </div>
    </div>
  );
}

export default Scanner;
