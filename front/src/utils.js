export async function jsonFetch(url) {
  let response = await fetch(url);
  return response.json();
}

export async function postForm(url, data) {
  let form = new FormData();
  for (let [key, value] of Object.entries(data)) {
    form.append(key, String(value));
  }
  return fetch(url, { method: "POST", body: form });
}
