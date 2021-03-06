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
  const [lastScan, setLastScan] = useState(null);

  let scan = useCallback(
    async (code) => {
      if (lastScan) {
        return;
      }

      navigator.vibrate(200);
      let response;

      response = await fetch(scanUrl(code, user, point));

      if (response.ok) {
        return setLastScan({ registration: await response.json(), code });
      }

      if (response.status === 404) {
        throw new Error("Not Found");
      }
    },
    [user, point]
  );

  let validateScan = useCallback(async () => {
    await postForm(scanUrl(lastScan.code, user, point), {
      type: "entrance",
    });

    setLastScan(null);
  }, [lastScan, user, point]);

  let cancelScan = useCallback(async () => {
    await postForm(scanUrl(lastScan.code, user, point), {
      type: "cancel",
    });

    setLastScan(null);
  }, [lastScan, user, point]);

  if (user !== null && point !== null) {
    return (
      <>
        <Scanner setPoint={setPoint} scan={scan} user={user} point={point} />
        {lastScan && (
          <Ticket
            registration={lastScan.registration}
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
