export default function FoundationPage() {
  return (
    <main>
      <header>
        <span className="brand">
          NFT
          <span className="brand-mark" aria-hidden="true">
            /
          </span>
        </span>
        <span className="company">NEXT-GEN FACTORY TECHNOLOGIES</span>
        <span className="phase">PHASE 0</span>
      </header>
      <section className="workspace" aria-labelledby="title">
        <p className="eyebrow">NFT MANUFACTURING INTELLIGENCE</p>
        <h1 id="title">
          A foundation for
          <br />a clearer shop floor.
        </h1>
        <p className="intro">
          The development foundation is in place. Operational workflows will be
          added in the next implementation phases.
        </p>
        <div className="status">
          <span className="status-label">WORKSPACE STATUS</span>
          <strong>No shop data connected</strong>
          <p>
            No machine readings, production records, or simulated results are
            displayed.
          </p>
        </div>
        <div className="boundaries" aria-label="Platform architecture">
          <article>
            <span className="number">01</span>
            <h2>NFT Command Center</h2>
            <p>Shop visibility built on authorized operational records.</p>
            <span className="tag">PLANNED · PHASE 2</span>
          </article>
          <article>
            <span className="number">02</span>
            <h2>NFT Insights</h2>
            <p>
              Deterministic metrics and evidence-based operational findings.
            </p>
            <span className="tag">PLANNED · PHASES 4–5</span>
          </article>
          <article>
            <span className="number">03</span>
            <h2>NFT Intelligence</h2>
            <p>Advisory explanations grounded in authorized evidence.</p>
            <span className="tag">PLANNED · PHASE 6</span>
          </article>
        </div>
      </section>
      <footer>
        <span>FOUNDATION RELEASE · 0.0.1</span>
        <span>Manual-first. Advisory-only.</span>
      </footer>
    </main>
  );
}
