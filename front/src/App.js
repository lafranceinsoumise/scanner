import React, { useCallback, useState } from "react";
import Scanner from "./Scanner";
import "./App.css";
import config from "./config";
import { Start } from "./Start";
import { Ticket } from "./Ticket";
import { postForm } from "./utils";

function scanUrl(code, user, point, event) {
  // Ajoute event dans l'URL si besoin
  let url = `${config.host}/code/${code}/?person=${encodeURIComponent(
    user
  )}&point=${encodeURIComponent(point)}`;
  if (event) {
    url += `&event=${encodeURIComponent(event)}`;
  }
  return url;
}

const App = (props) => {
  const [user, setUser] = useState(null);
  const [point, setPoint] = useState(null);
  const [event, setEvent] = useState(null);
  const [currentScan, setCurrentScan] = useState(null);
  const [loading, setLoading] = useState(false);

  let scan = useCallback(
    async (code) => {
      navigator.vibrate =
        navigator.vibrate ||
        navigator.webkitVibrate ||
        navigator.mozVibrate ||
        navigator.msVibrate;
      if (navigator.vibrate) {
        navigator.vibrate(200);
      }

      let response;

      setLoading(true);

      response = await fetch(scanUrl(code, user, point, event));

      if (response.ok) {
        setCurrentScan({ registration: await response.json(), code });
      }
      setLoading(false);

      if (response.status === 404) {
        throw new Error("Not Found");
      }
    },
    [user, point, event]
  );

  let validateScan = useCallback(async () => {
    await postForm(scanUrl(currentScan.code, user, point, event), {
      type: "entrance",
    });

    setCurrentScan(null);
  }, [currentScan, user, point, event]);

  let cancelScan = useCallback(async () => {
    await postForm(scanUrl(currentScan.code, user, point, event), {
      type: "cancel",
    });

    setCurrentScan(null);
  }, [currentScan, user, point, event]);

  if (user !== null && point !== null) {
    return (
      <>
        <Scanner
          setPoint={setPoint}
          loading={loading}
          scan={loading || currentScan ? null : scan}
          user={user}
          point={point}
          event={event}
        />
        {(currentScan && event) && (
          <Ticket
            registration={currentScan.registration}
            selectedEvent={event}
            validateScan={validateScan}
            cancelScan={cancelScan}
          />
        )}
      </>
    );
  }

  return (
    <Start
      user={user}
      setUser={setUser}
      setPoint={setPoint}
      setEvent={setEvent}
      event={event}
      point={point}
    />
  );
};

export default App;
