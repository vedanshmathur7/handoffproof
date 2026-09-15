function App() {
  return (
    <main className="shell">
      <header className="hero">
        <p className="eyebrow">Workflow evidence, without guesswork</p>
        <h1>HandoffProof</h1>
        <p className="intro">
          Check whether every source lead reached its destination correctly.
        </p>
      </header>

      <section className="empty-state" aria-labelledby="empty-state-title">
        <div className="status-dot" aria-hidden="true" />
        <div>
          <h2 id="empty-state-title">No reconciliation runs yet</h2>
          <p>
            CSV imports and matching arrive in the next phases. The foundation is
            ready for them.
          </p>
        </div>
      </section>
    </main>
  );
}

export default App;
