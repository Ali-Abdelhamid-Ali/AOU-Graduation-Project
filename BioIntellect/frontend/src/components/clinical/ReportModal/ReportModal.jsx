import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { reportsAPI } from '@/services/api/endpoints'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import styles from './ReportModal.module.css'

/**
 * ReportModal — full-screen animated popup for doctor to write / edit / save / discard a report.
 *
 * Props:
 *  result       — the ECG or MRI result object
 *  resultType   — 'ecg' | 'mri'
 *  patientId    — string
 *  doctorId     — string
 *  onClose      — () => void
 *  onSaved      — (report) => void
 */
export const ReportModal = ({ result, resultType, patientId, doctorId, onClose, onSaved }) => {
  const [report, setReport]       = useState(null)   // existing report from DB
  const [title, setTitle]         = useState('')
  const [summary, setSummary]     = useState('')
  const [content, setContent]     = useState('')     // doctor free-text body
  const [loading, setLoading]     = useState(true)
  const [saving, setSaving]       = useState(false)
  const [error, setError]         = useState('')
  const [saved, setSaved]         = useState(false)
  const textareaRef               = useRef(null)

  // ── Derive AI default text from the result ──────────────────────────
  const aiDefaultContent = deriveDefaultContent(result, resultType)

  // ── Load existing report (if any) ──────────────────────────────────
  useEffect(() => {
    if (!result?.id) return
    let cancelled = false
    const load = async () => {
      setLoading(true)
      try {
        const res = await reportsAPI.getByResult(resultType, result.id)
        if (!cancelled && res.data) {
          const r = res.data
          setReport(r)
          setTitle(r.title || '')
          setSummary(r.summary || '')
          setContent(r.content?.body || aiDefaultContent)
        } else if (!cancelled) {
          // No existing report — prefill with AI output
          setTitle(deriveDefaultTitle(result, resultType))
          setSummary(deriveDefaultSummary(result, resultType))
          setContent(aiDefaultContent)
        }
      } catch {
        if (!cancelled) {
          setTitle(deriveDefaultTitle(result, resultType))
          setSummary(deriveDefaultSummary(result, resultType))
          setContent(aiDefaultContent)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [result?.id, resultType]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Auto-grow textarea ──────────────────────────────────────────────
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [content])

  // ── Save (create or update) ─────────────────────────────────────────
  const handleSave = async (andFinalize = false) => {
    if (!title.trim()) { setError('Title is required.'); return }
    setSaving(true); setError('')
    try {
      const payload = {
        title,
        summary,
        content: { body: content },
        ...(andFinalize ? { status: 'approved' } : { status: 'draft' }),
      }

      let saved_report
      if (report?.id) {
        const res = await reportsAPI.update(report.id, payload)
        saved_report = res.data
        if (andFinalize) await reportsAPI.approve(report.id, '')
      } else {
        const createPayload = {
          patient_id: patientId,
          doctor_id: doctorId,
          report_type: resultType === 'ecg' ? 'ecg_analysis' : 'mri_analysis',
          [`${resultType}_result_id`]: result.id,
          generated_by_model: result.analyzed_by_model || 'BioIntellect-AI',
          model_version: result.model_version || '1.0',
          ...payload,
        }
        const res = await reportsAPI.create(createPayload)
        saved_report = res.data
        if (andFinalize && saved_report?.id) {
          await reportsAPI.approve(saved_report.id, '')
        }
      }

      setReport(saved_report)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
      onSaved?.(saved_report)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to save report.'))
    } finally {
      setSaving(false)
    }
  }

  const handleDiscard = async () => {
    if (!report?.id) { onClose(); return }
    if (!window.confirm('Discard this draft report? This cannot be undone.')) return
    setSaving(true)
    try {
      await reportsAPI.discard(report.id)
      onClose()
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to discard report.'))
    } finally {
      setSaving(false)
    }
  }

  const isFinalized = report?.is_final === true

  return (
    <AnimatePresence>
      <motion.div
        className={styles.backdrop}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <motion.div
          className={styles.modal}
          initial={{ opacity: 0, y: 40, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 24, scale: 0.97 }}
          transition={{ type: 'spring', stiffness: 320, damping: 28 }}
        >
          {/* ── Header ── */}
          <div className={styles.header}>
            <div className={styles.headerMeta}>
              <span className={`${styles.badge} ${resultType === 'ecg' ? styles.ecg : styles.mri}`}>
                {resultType.toUpperCase()}
              </span>
              {isFinalized && <span className={styles.badgeFinal}>Finalized</span>}
              {report?.status === 'draft' && <span className={styles.badgeDraft}>Draft</span>}
            </div>
            <h2 className={styles.modalTitle}>Clinical Report</h2>
            <p className={styles.modalSub}>
              {result?.patient_name || 'Patient'} ·{' '}
              {new Date(result?.created_at || Date.now()).toLocaleDateString()}
            </p>
            <button className={styles.closeBtn} onClick={onClose} aria-label="Close">✕</button>
          </div>

          {loading ? (
            <div className={styles.loadingState}>
              <div className={styles.spinner} />
              <p>Loading report…</p>
            </div>
          ) : (
            <div className={styles.body}>
              {/* ── AI Default block ── */}
              <section className={styles.aiBlock}>
                <p className={styles.aiLabel}>AI Analysis Summary</p>
                <p className={styles.aiText}>{aiDefaultContent}</p>
              </section>

              {/* ── Doctor fields ── */}
              <section className={styles.form}>
                <label className={styles.fieldLabel}>
                  Report Title *
                  <input
                    className={styles.input}
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    disabled={isFinalized}
                    placeholder="e.g. ECG Analysis — Sinus Tachycardia"
                  />
                </label>

                <label className={styles.fieldLabel}>
                  Short Summary
                  <input
                    className={styles.input}
                    value={summary}
                    onChange={(e) => setSummary(e.target.value)}
                    disabled={isFinalized}
                    placeholder="One-line clinical impression"
                  />
                </label>

                <label className={styles.fieldLabel}>
                  Full Clinical Report
                  <textarea
                    ref={textareaRef}
                    className={styles.textarea}
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    disabled={isFinalized}
                    placeholder="Write your full clinical report here…"
                    rows={8}
                  />
                </label>
              </section>

              {error && <p className={styles.errorMsg}>{error}</p>}
              {saved && <p className={styles.successMsg}>Saved successfully.</p>}
            </div>
          )}

          {/* ── Footer actions ── */}
          {!loading && (
            <div className={styles.footer}>
              {!isFinalized && (
                <>
                  <button
                    className={styles.btnDiscard}
                    onClick={handleDiscard}
                    disabled={saving}
                  >
                    {report?.id ? 'Discard Draft' : 'Cancel'}
                  </button>
                  <button
                    className={styles.btnDefer}
                    onClick={() => handleSave(false)}
                    disabled={saving}
                  >
                    {saving ? 'Saving…' : 'Save Draft'}
                  </button>
                  <button
                    className={styles.btnSave}
                    onClick={() => handleSave(true)}
                    disabled={saving}
                  >
                    {saving ? 'Saving…' : 'Save & Finalize'}
                  </button>
                </>
              )}
              {isFinalized && (
                <button className={styles.btnClose} onClick={onClose}>Close</button>
              )}
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function deriveDefaultTitle(result, type) {
  if (type === 'ecg') {
    const dx = result?.rhythm_classification || result?.primary_diagnosis || 'ECG Analysis'
    return `ECG Report — ${dx}`
  }
  const dx = result?.tumor_detected ? 'Tumor Detected' : 'No Significant Finding'
  return `MRI Segmentation Report — ${dx}`
}

function deriveDefaultSummary(result, type) {
  if (type === 'ecg') {
    return result?.ai_interpretation || result?.rhythm_classification || ''
  }
  return result?.ai_interpretation || ''
}

function deriveDefaultContent(result, type) {
  if (!result) return ''

  if (type === 'ecg') {
    // Use full clinical report text if available (preferred)
    if (result.clinical_report) return result.clinical_report

    const lines = [
      result.ai_interpretation && `Interpretation: ${result.ai_interpretation}`,
      result.rhythm_classification && `Rhythm: ${result.rhythm_classification}`,
      result.heart_rate && `Heart Rate: ${result.heart_rate} bpm`,
      result.risk_score != null && `Risk Score: ${result.risk_score}%`,
      result.ai_recommendations?.length &&
        `Recommendations:\n${result.ai_recommendations.map((r) => `• ${r}`).join('\n')}`,
    ].filter(Boolean)
    return lines.join('\n\n')
  }

  // MRI
  const lines = [
    result.ai_interpretation && `Interpretation: ${result.ai_interpretation}`,
    result.tumor_detected != null && `Tumor Detected: ${result.tumor_detected ? 'Yes' : 'No'}`,
    result.confidence_score != null && `Confidence: ${(result.confidence_score * 100).toFixed(1)}%`,
    result.ai_recommendations?.length &&
      `Recommendations:\n${result.ai_recommendations.map((r) => `• ${r}`).join('\n')}`,
  ].filter(Boolean)
  return lines.join('\n\n')
}

export default ReportModal
