import React, { useCallback, useState } from "react";
import Scanner from "./Scanner";
import "./App.css";
import config from "./config";
import { Start } from "./Start";
import { Ticket } from "./Ticket";
import { postForm } from "./utils";

function scanUrl(code, user, point) {
  return `${config.host}/code/${code}/?person=${encodeURIComponent(
    user
  )}&point=${encodeURIComponent(point)}`;
}

const App = (props) => {
  const [user, setUser] = useState(null);
  const [point, setPoint] = useState(null);
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

      response = await fetch(scanUrl(code, user, point));

      if (response.ok) {
        setCurrentScan({ registration: await response.json(), code });
      }
      setLoading(false);

      if (response.status === 404) {
        throw new Error("Not Found");
      }
    },
    [user, point]
  );

  let validateScan = useCallback(async () => {
    await postForm(scanUrl(currentScan.code, user, point), {
      type: "entrance",
    });

    setCurrentScan(null);
  }, [currentScan, user, point]);

  let cancelScan = useCallback(async () => {
    await postForm(scanUrl(currentScan.code, user, point), {
      type: "cancel",
    });

    setCurrentScan(null);
  }, [currentScan, user, point]);

  if (user !== null && point !== null) {
    return (
      <>
        <Scanner
          setPoint={setPoint}
          loading={loading}
          scan={loading || currentScan ? null : scan}
          user={user}
          point={point}
        />
        {currentScan && (
          <Ticket
            registration={currentScan.registration}
            validateScan={validateScan}
            cancelScan={cancelScan}
          />
        )}
      </>
    );
  }

  return <Start user={user} setUser={setUser} setPoint={setPoint} />;
};

export default App;
