import React, { useCallback, useEffect, useRef, useState } from "react";
import cursorFill from "bootstrap-icons/icons/cursor-fill.svg";
import person from "bootstrap-icons/icons/person.svg";
import people from "bootstrap-icons/icons/people.svg";
import X from "bootstrap-icons/icons/x.svg";
import useSWR, { mutate } from "swr";
import { Html5Qrcode } from "html5-qrcode";

import config from "./config";
import { jsonFetch, postForm } from "./utils";

function Scanner({ scan, setPoint, user, point, loading }) {
  const [error, setError] = useState(false);
  const [pause, setPause] = useState(false);

  const scanner = useRef(null);
  const cameras = useRef(null);
  const activeCameraIndex = useRef(null);
  const scanRef = useRef(null);

  const { data: events } = useSWR(`${config.host}/api/events`, jsonFetch);

  const displayError = useCallback((message) => {
    setError(message || "Impossible de lire le billet.");
    setTimeout(() => setError(false), 3000);
  }, []);

  const startCamera = useCallback(
    async (forcedCameraId = null) => {
      const previewElement = document.getElementById("preview");
      if (!previewElement) {
        console.error("Élément #preview introuvable dans le DOM.");
        return displayError("Erreur interne : aperçu non disponible.");
      }

      try {
        if (!scanner.current) {
          scanner.current = new Html5Qrcode("preview");
        }

        if (!cameras.current) {
          cameras.current = await Html5Qrcode.getCameras();
          if (!cameras.current.length) {
            return displayError("Aucune caméra détectée.");
          }
        }

        if (activeCameraIndex.current === null) {
          let savedCam = +localStorage.getItem("cameraIndex");
          if (
            Number.isInteger(savedCam) &&
            savedCam >= 0 &&
            savedCam < cameras.current.length
          ) {
            activeCameraIndex.current = savedCam;
          } else {
            activeCameraIndex.current = 0;
          }
        }

        const selectedCamId =
          forcedCameraId || cameras.current[activeCameraIndex.current].id;

        await scanner.current.start(
          selectedCamId,
          { fps: 5 },
          async (decodedText) => {
            const scan = scanRef.current;
            if (!scan) return;
            try {
              await scan(decodedText);
            } catch (err) {
              if (err.message === "Not Found") {
                return displayError("Billet inconnu.");
              }
              return displayError(err.message);
            }
          },
          (errorMessage) => {
            console.warn("Scan non valide :", errorMessage);
          }
        );
      } catch (err) {
        console.error("Erreur au démarrage de la caméra :", err);
        displayError(
          "Impossible d'accéder à la caméra. Vérifie les autorisations."
        );
      }
    },
    [displayError]
  );

  const stopCamera = useCallback(async () => {
    if (scanner.current) {
      try {
        await scanner.current.stop();
      } catch (err) {
        console.warn("Erreur à l'arrêt de la caméra :", err);
      }
      await scanner.current.clear();
    }
  }, []);

  const changeCamera = useCallback(async () => {
    if (!cameras.current?.length) return;
    await stopCamera();
    activeCameraIndex.current =
      (activeCameraIndex.current + 1) % cameras.current.length;
    localStorage.setItem("cameraIndex", activeCameraIndex.current);
    await startCamera();
  }, [startCamera, stopCamera]);

  useEffect(() => {
    const timer = setTimeout(() => {
      startCamera();
    }, 300);
    return () => {
      clearTimeout(timer);
      stopCamera();
    };
  }, [startCamera, stopCamera]);

  useEffect(() => {
    scanRef.current = scan;
  }, [scan]);

  let eventName =
    events && events[0].scan_points.find((e) => e.id === point)?.name;
  let eventCount =
    events && events[0].scan_points.find((e) => e.id === point)?.count;

  return (
    <>
      <div style={{ backgroundColor: "#fff", width: "100%" }} className="container-fluid">
        <div className="row" style={{ marginTop: "20px" }}>
          <div className="col-xs-6">
            <p>
              <img src={person} alt="Utilisateur⋅ice" /> {user}
            </p>
            <p>
              <img src={cursorFill} alt="Point de contrôle" /> {eventName}{" "}
              <img
                onClick={() => setPoint(null)}
                className="pull-right"
                src={X}
                alt="Changer le lieu"
                role="button"
                style={{ cursor: "pointer" }}
              />
            </p>
          </div>
          <div className="col-xs-6">
            {eventCount !== null && (
              <>
                <p>
                  <img src={people} alt="Compteur" /> {eventCount}
                </p>
                <button
                  className="btn btn-info btn-sm"
                  onClick={async () => {
                    await postForm(`${config.host}/reset/`, { point });
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

      <div id="camera-container" className="container">
        <div id="preview" />
      </div>

      <div>
        {loading && (
          <div className="container">
            <div className="alert alert-info">Chargement…</div>
          </div>
        )}
        {error && (
          <div className="container">
            <div className="alert alert-danger">{error}</div>
          </div>
        )}
        <button
          className="btn btn-lg btn-success btn-block"
          onClick={changeCamera}
        >
          Changer la caméra
        </button>
        <button
          className="btn btn-lg btn-danger btn-block"
          onClick={() => {
            setPause(!pause);
            pause ? startCamera() : stopCamera();
          }}
        >
          {pause ? "Relancer la caméra" : "Mettre en pause la caméra"}
        </button>
      </div>
    </>
  );
}

export default Scanner;
