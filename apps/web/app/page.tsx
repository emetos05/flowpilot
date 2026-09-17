import styles from "./page.module.css";

export const dynamic = "force-dynamic";

export default async function Home() {
  let healthy = false;
  try {
    const baseUrl = process.env.API_BASE_URL || "http://127.0.0.1:8000";
    const response = await fetch(`${baseUrl.replace(/\/$/, "")}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    if (response.ok) {
      const data = await response.json();
      healthy = data?.status === "ok";
    }
  } catch {
    // Keep the page usable when the API is unavailable or times out.
  }
  return (
    <main className={styles.main}>
      <p className={styles.eyebrow}>FLOWPILOT · DAY 1</p>
      <h1>A foundation for simpler workflows.</h1>
      <p>Bring routine business work into one place, with a connected web app and API.</p>
      <section className={styles.card} aria-labelledby="health-title">
        <h2 id="health-title">Backend connection</h2>
        <p role="status" className={healthy ? styles.healthy : styles.unavailable}>
          {healthy ? "Backend is healthy" : "Backend is unavailable"}
        </p>
        <p>{healthy
          ? "FlowPilot successfully connected to the API."
          : "The API could not be reached or returned an unexpected response. Try again shortly."}</p>
        <form action="/" method="get">
          <button className={styles.button} type="submit">Check again</button>
        </form>
      </section>
    </main>
  );
}
