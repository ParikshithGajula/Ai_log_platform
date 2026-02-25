import React, { useState, useRef, useEffect } from 'react';
import { uploadLog, getJob } from '../api/client';

/**
 * Key React Concept: useEffect with setInterval for polling — always clear 
 * the interval in the cleanup function or it will keep running after the 
 * component unmounts.
 */
export default function LogUploader({ onComplete }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("Queued");
  const [progress, setProgress] = useState(0);
  const [jobId, setJobId] = useState(null);
  const [displayText, setDisplayText] = useState("");
  const intervalRef = useRef(null);

  // Poll job status every 2 seconds when processing
  useEffect(() => {
    if (status === "Processing" && jobId) {
      intervalRef.current = setInterval(async () => {
        try {
          const job = await getJob(jobId);
          if (job.status === "completed") {
            setStatus("Completed");
            setProgress(100);
            setDisplayText(`Done! ${job.processed_count || 0} logs processed.`);
            clearInterval(intervalRef.current);
            if (onComplete) onComplete();
          } else if (job.status === "failed") {
            setStatus("Failed");
            setDisplayText(`Error: ${job.error || "Unknown error"}`);
            clearInterval(intervalRef.current);
          }
        } catch (error) {
          console.error("Error fetching job:", error);
        }
      }, 2000);
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [status, jobId, onComplete]);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setStatus("Queued");
      setProgress(0);
      setJobId(null);
      setDisplayText("");
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setStatus("Queued");
      setProgress(0);
      setJobId(null);
      setDisplayText("");
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus("Uploading");
    setProgress(0);
    setJobId(null);
    setDisplayText("");

    try {
      const result = await uploadLog(file, (percent) => {
        setProgress(percent);
      });
      setJobId(result.job_id);
      setStatus("Processing");
      setDisplayText("Processing...");
    } catch (error) {
      setStatus("Failed");
      setDisplayText(`Upload failed: ${error.message}`);
    }
  };

  return (
    <div className="mb-6">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className="border-2 border-dashed border-muted rounded-lg p-8 text-center hover:border-accent transition"
      >
        <div className="mb-4">
          <div className="text-lg font-semibold mb-2">📁 Upload Log File</div>
          <p className="text-muted text-sm mb-4">Drag and drop or click to browse</p>

          <input
            type="file"
            onChange={handleFileSelect}
            disabled={status === "Uploading" || status === "Processing"}
            className="hidden"
            id="file-input"
          />
          <label
            htmlFor="file-input"
            className="inline-block cursor-pointer px-6 py-2 bg-accent text-surface rounded font-semibold hover:opacity-90 transition disabled:opacity-50"
          >
            Choose File
          </label>
        </div>

        {file && (
          <div className="mt-4 p-4 bg-surface rounded border border-border">
            <div className="text-sm text-muted mb-1">Selected:</div>
            <div className="text-text font-semibold">
              {file.name} ({(file.size / 1024).toFixed(2)} KB)
            </div>
          </div>
        )}

        {(status === "Uploading" || status === "Processing") && (
          <div className="mt-4">
            <div className="w-full bg-surface rounded-full h-2 overflow-hidden border border-border">
              <div
                className="bg-gradient-to-r from-accent to-blue-400 h-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <div className="text-sm text-accent mt-2 font-semibold">{progress}%</div>
          </div>
        )}

        {displayText && (
          <div className="mt-4 p-3 bg-surface rounded border border-border text-sm text-text">
            {displayText}
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || status !== "Queued"}
          className="mt-4 px-6 py-2 bg-accent text-surface rounded font-semibold hover:opacity-90 disabled:opacity-50 transition"
        >
          {status === "Uploading"
            ? `Uploading (${progress}%)...`
            : status === "Processing"
            ? "Processing..."
            : "Upload"}
        </button>
      </div>
    </div>
  );
}
