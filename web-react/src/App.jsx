import { lazy, Suspense, useEffect, useState } from 'react';
import {
  AlertTriangle,
  ArrowDownToLine,
  Atom,
  BookOpen,
  CheckCircle2,
  Database,
  FileText,
  GitCommit,
  Microscope,
  Orbit,
  ShieldCheck,
} from 'lucide-react';

const JwstHero = lazy(() => import('./JwstHero.jsx'));

const sectionLinks = [
  ['measurements', 'Measurements'],
  ['confidence', 'Confidence'],
  ['figures', 'Figure records'],
  ['provenance', 'Provenance'],
  ['validation', 'Validation'],
  ['warnings', 'Warnings'],
  ['method', 'Method'],
  ['downloads', 'Downloads'],
];

function useJson(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  useEffect(() => {
    let cancelled = false;
    fetch(path)
      .then((response) => {
        if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
        return response.json();
      })
      .then((data) => {
        if (!cancelled) setState({ data, error: null, loading: false });
      })
      .catch((error) => {
        if (!cancelled) setState({ data: null, error, loading: false });
      });
    return () => { cancelled = true; };
  }, [path]);
  return state;
}

function formatEstimate(value) {
  return typeof value === 'number' ? value.toPrecision(4) : String(value);
}

function SectionHeading({ eyebrow, title, icon: Icon }) {
  return (
    <header className="section-heading">
      <span className="section-icon"><Icon size={17} /></span>
      <div>
        <p>{eyebrow}</p>
        <h2>{title}</h2>
      </div>
    </header>
  );
}

function MetricCard({ metric, index }) {
  const hasUncertainty = metric.uncertainty_low != null && metric.uncertainty_high != null;
  return (
    <article className={`metric-card metric-${index + 1}`}>
      <p className="metric-index">0{index + 1}</p>
      <p className="metric-name">{metric.name.replace(/_/g, ' ')}</p>
      <p className="metric-value">
        {formatEstimate(metric.estimate)}
        <span>{metric.units}</span>
      </p>
      {hasUncertainty && (
        <p className="metric-ci">
          95% CI&nbsp; {metric.uncertainty_low.toPrecision(3)}–{metric.uncertainty_high.toPrecision(3)}
        </p>
      )}
      <p className="metric-sample">sample n = {metric.sample_size}</p>
    </article>
  );
}

function inverseNormalCDF(p) {
  if (p <= 0 || p >= 1) return NaN;
  const a = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.357751867269, -30.66479806614716, 2.506628277459239];
  const b = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572];
  const c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
  const d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416];
  const pLow = 0.02425;
  const pHigh = 1 - pLow;
  let q;
  let r;
  if (p < pLow) {
    q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
      / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  if (p <= pHigh) {
    q = p - 0.5;
    r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
      / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  q = Math.sqrt(-2 * Math.log(1 - p));
  return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
    / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
}

function ConfidenceExplorer({ metrics }) {
  const withCI = (metrics || []).filter(
    (metric) => metric.uncertainty_low != null && metric.uncertainty_high != null,
  );
  const [selected, setSelected] = useState(null);
  const [confidence, setConfidence] = useState(95);

  useEffect(() => {
    if (!selected && withCI.length > 0) setSelected(withCI[0].name);
  }, [withCI, selected]);

  if (withCI.length === 0) {
    return <p className="empty-note">No interval-bearing metrics are present in the loaded summary.</p>;
  }
  const metric = withCI.find((item) => item.name === selected) ?? withCI[0];
  const sigma = ((metric.uncertainty_high - metric.uncertainty_low) / 2) / 1.959963984540054;
  const zLevel = inverseNormalCDF(0.5 + confidence / 200);
  const lo = metric.estimate - zLevel * sigma;
  const hi = metric.estimate + zLevel * sigma;

  return (
    <div className="confidence-grid">
      <div className="confidence-control">
        <label htmlFor="metric-select">Metric</label>
        <select id="metric-select" value={metric.name} onChange={(event) => setSelected(event.target.value)}>
          {withCI.map((item) => (
            <option key={item.name} value={item.name}>{item.name.replace(/_/g, ' ')}</option>
          ))}
        </select>
        <label htmlFor="confidence-range">
          Confidence level <strong>{confidence.toFixed(1)}%</strong>
        </label>
        <input
          id="confidence-range"
          type="range"
          min="50"
          max="99.9"
          step="0.1"
          value={confidence}
          onChange={(event) => setConfidence(Number(event.target.value))}
        />
      </div>
      <div className="interval-readout">
        <p>Approximate interval</p>
        <strong>[{lo.toPrecision(4)}, {hi.toPrecision(4)}]</strong>
        <span>{metric.units} · estimate {metric.estimate.toPrecision(4)} · n = {metric.sample_size}</span>
      </div>
      <p className="confidence-note">
        This client-side sensitivity view rescales the reported 95% bootstrap interval under a
        normal sampling approximation. It does not rerun the bootstrap; the 95% result in the
        loaded summary remains the computed result from <code>uncertainty.py</code>.
      </p>
    </div>
  );
}

function WarningStatus({ state }) {
  if (state.loading) return <p className="warning-pending">Reading results/warnings.json…</p>;
  if (state.error) {
    return (
      <div className="warning-error" role="alert">
        <AlertTriangle size={20} />
        <div><strong>Warning file unavailable</strong><p>{String(state.error)}</p></div>
      </div>
    );
  }
  if (!Array.isArray(state.data)) {
    return (
      <div className="warning-error" role="alert">
        <AlertTriangle size={20} />
        <p>The warning file loaded, but its top-level value is not a list.</p>
      </div>
    );
  }
  if (state.data.length === 0) {
    return (
      <div className="warning-clear">
        <CheckCircle2 size={23} />
        <div>
          <strong>No warnings recorded in results/warnings.json.</strong>
          <p>The live warning artifact loaded successfully and currently contains an empty list.</p>
        </div>
      </div>
    );
  }
  return (
    <ol className="warning-list">
      {state.data.map((warning, index) => (
        <li key={`${index}-${String(warning)}`}>
          <span>{String(index + 1).padStart(2, '0')}</span>
          {typeof warning === 'string' ? warning : JSON.stringify(warning)}
        </li>
      ))}
    </ol>
  );
}

function FigureGallery({ figures }) {
  return (
    <div className="figure-stack">
      {figures.map((figure, index) => (
        <figure className="figure-record" key={figure.id}>
          <div className="figure-copy">
            <p>Figure {String(index + 1).padStart(2, '0')}</p>
            <h3>{figure.label}</h3>
            <span>Production simulation · SVG export</span>
            <a href={`./figures/${figure.id}.png`} download>
              <ArrowDownToLine size={15} /> 300 dpi PNG
            </a>
          </div>
          <div className="figure-frame">
            <img src={`./figures/${figure.id}.svg`} alt={figure.label} />
          </div>
        </figure>
      ))}
    </div>
  );
}

export default function App() {
  const project = useJson('./project.json');
  const summary = useJson('./results/summary.json');
  const warnings = useJson('./results/warnings.json');
  const benchmarks = useJson('./results/benchmarks.json');

  if (project.loading) return <main className="page-state">Loading instrument dossier…</main>;
  if (project.error || !project.data) {
    return <main className="page-state page-error">Could not load project.json: {String(project.error)}</main>;
  }

  const p = project.data;
  const runLabel = summary.data?.provenance?.run_label;
  const isSmallTrialDemo = runLabel === 'demo' || runLabel === 'custom'
    || summary.data?.data_kind === 'synthetic_smoke_test';

  return (
    <main className="site-shell">
      <header className="mission-hero">
        <nav className="masthead" aria-label="Project identity">
          <a href="#measurements" className="wordmark"><Orbit size={19} /> SHUTTER / LIGHT</a>
          <span>Experiment 08 · NIRSpec MSA</span>
        </nav>
        <div className="hero-copy">
          <p className="hero-kicker">{p.category}</p>
          <h1>{p.title}</h1>
          <p className="hero-question">{p.question}</p>
          <div className="hero-badges">
            <span>{p.status}</span>
            <span>Priority {p.priority}/10</span>
            <span>{p.productionTrials.toLocaleString()} production trials</span>
            <span className={isSmallTrialDemo ? 'badge-demo' : 'badge-ready'}>
              {isSmallTrialDemo ? 'Small-trial demo results' : 'Full Monte Carlo results'}
            </span>
          </div>
        </div>
        <div className="hero-stage">
          <Suspense fallback={<div className="hero-fallback">Building procedural instrument view…</div>}>
            <JwstHero />
          </Suspense>
        </div>
      </header>

      {isSmallTrialDemo && (
        <aside className="demo-banner">
          <AlertTriangle size={19} />
          <p>
            The loaded artifacts use a small trial count for fast checks. A production run uses
            {` ${p.productionTrials.toLocaleString()} `}trials. Every result is synthetic Monte Carlo
            output based on verified instrument parameters, never NIRSpec telemetry.
          </p>
        </aside>
      )}

      <div className="dossier-layout">
        <aside className="index-rail">
          <p className="rail-label">Experiment index</p>
          <nav aria-label="Experiment sections">
            {sectionLinks.map(([id, label], index) => (
              <a href={`#${id}`} key={id}><span>{String(index + 1).padStart(2, '0')}</span>{label}</a>
            ))}
          </nav>
          <div className="boundary-note">
            <ShieldCheck size={18} />
            <p>Instrument-physics QA sandbox. Not an official path-loss correction.</p>
          </div>
        </aside>

        <div className="dossier-content">
          <section id="measurements" className="dossier-section">
            <SectionHeading eyebrow="Production output" title="Throughput measurements" icon={Microscope} />
            {summary.loading && <p className="empty-note">Reading results/summary.json…</p>}
            {summary.error && <p className="error-note">Could not load the result summary.</p>}
            {summary.data?.metrics?.length > 0 ? (
              <div className="metric-mosaic">
                {summary.data.metrics.slice(0, 6).map((metric, index) => (
                  <MetricCard key={metric.name} metric={metric} index={index} />
                ))}
              </div>
            ) : !summary.loading && !summary.error && (
              <p className="empty-note">No result metrics yet. Run scripts/run_analysis.py first.</p>
            )}
          </section>

          <section id="confidence" className="dossier-section confidence-section">
            <SectionHeading eyebrow="Interactive check" title="Confidence-level explorer" icon={Atom} />
            <ConfidenceExplorer metrics={summary.data?.metrics} />
          </section>

          <section id="figures" className="dossier-section figures-section">
            <SectionHeading eyebrow="Generated evidence" title="Figure records" icon={BookOpen} />
            <FigureGallery figures={p.figures} />
          </section>

          <section id="provenance" className="split-section">
            <article className="panel provenance-panel">
              <SectionHeading eyebrow="Traceability" title="Provenance boundary" icon={GitCommit} />
              <p className="body-copy">{p.novelty}</p>
              {summary.data?.provenance && (
                <dl className="provenance-list">
                  <div><dt>Git commit</dt><dd>{summary.data.provenance.git_commit}</dd></div>
                  <div><dt>Config sha256</dt><dd>{summary.data.provenance.config_sha256 ?? 'n/a'}</dd></div>
                  <div><dt>Package version</dt><dd>{summary.data.provenance.package_version}</dd></div>
                </dl>
              )}
              <p className="readiness-note"><AlertTriangle size={17} /> Public readiness requires validation and provenance checks.</p>
            </article>
            <article id="validation" className="panel validation-panel">
              <SectionHeading eyebrow="Acceptance tests" title="Validation contract" icon={ShieldCheck} />
              <ol className="numbered-list">
                {p.validationContract.map((item, index) => (
                  <li key={item}><span>{String(index + 1).padStart(2, '0')}</span>{item}</li>
                ))}
              </ol>
            </article>
          </section>

          <section id="warnings" className="dossier-section warnings-section">
            <SectionHeading eyebrow="Live artifact" title="Warnings" icon={AlertTriangle} />
            <WarningStatus state={warnings} />
          </section>

          <section id="method" className="dossier-section method-section">
            <SectionHeading eyebrow="Model definition" title="Method and boundaries" icon={FileText} />
            <div className="method-grid">
              <article>
                <h3>Methodology</h3>
                <p>{p.methodology}</p>
              </article>
              <article>
                <h3>Assumptions</h3>
                <ul>{p.assumptions.map((item) => <li key={item}>{item}</li>)}</ul>
              </article>
              <article>
                <h3>Limitations</h3>
                <ul>{p.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
              </article>
            </div>
          </section>

          <section id="downloads" className="downloads-section">
            <article>
              <SectionHeading eyebrow="Reproducibility" title="Downloads" icon={Database} />
              <div className="download-links">
                <a href="./manifest.csv" download>data/manifest.csv</a>
                <a href="./results/summary.json" download>results/summary.json</a>
                {benchmarks.data && <a href="./results/benchmarks.json" download>results/benchmarks.json</a>}
              </div>
              <p>The manifest records the source, retrieval time, digest, selection reason, and terms for every verified instrument parameter used by the model.</p>
            </article>
            <article className="citation-card">
              <p>Citation / licence</p>
              <h2>{p.citation.author}</h2>
              <span>{p.citation.license}</span>
              <a href={p.citation.repository}>{p.citation.repository}</a>
            </article>
          </section>
        </div>
      </div>
    </main>
  );
}
