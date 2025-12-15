"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Slider } from "@/components/ui/slider"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { CheckCircle2, XCircle, Loader2 } from "lucide-react"

interface OutcomeRecorderProps {
  capsuleId: string
  predictedOutcome?: string
  onSuccess?: () => void
  onCancel?: () => void
}

interface OutcomeData {
  capsule_id: string
  predicted_outcome?: string
  actual_outcome: string
  outcome_quality_score?: number
  validation_method?: string
  validator_id?: string
  notes?: string
}

export function OutcomeRecorder({
  capsuleId,
  predictedOutcome,
  onSuccess,
  onCancel,
}: OutcomeRecorderProps) {
  const [actualOutcome, setActualOutcome] = useState("")
  const [qualityScore, setQualityScore] = useState([0.8])
  const [validationMethod, setValidationMethod] = useState<string>("user_feedback")
  const [validatorId, setValidatorId] = useState("")
  const [notes, setNotes] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitStatus, setSubmitStatus] = useState<"idle" | "success" | "error">("idle")
  const [errorMessage, setErrorMessage] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!actualOutcome.trim()) {
      setErrorMessage("Actual outcome is required")
      setSubmitStatus("error")
      return
    }

    setIsSubmitting(true)
    setSubmitStatus("idle")
    setErrorMessage("")

    const outcomeData: OutcomeData = {
      capsule_id: capsuleId,
      actual_outcome: actualOutcome,
      outcome_quality_score: qualityScore[0],
      validation_method: validationMethod,
      notes: notes.trim() || undefined,
    }

    if (predictedOutcome) {
      outcomeData.predicted_outcome = predictedOutcome
    }

    if (validatorId.trim()) {
      outcomeData.validator_id = validatorId
    }

    try {
      const response = await fetch("/outcomes", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(outcomeData),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to record outcome: ${response.statusText}`)
      }

      setSubmitStatus("success")

      // Reset form after successful submission
      setTimeout(() => {
        setActualOutcome("")
        setQualityScore([0.8])
        setValidationMethod("user_feedback")
        setValidatorId("")
        setNotes("")
        setSubmitStatus("idle")
        onSuccess?.()
      }, 2000)
    } catch (error) {
      console.error("Error recording outcome:", error)
      setErrorMessage(error instanceof Error ? error.message : "Unknown error occurred")
      setSubmitStatus("error")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span className="text-2xl">📊</span>
          Record Outcome
        </CardTitle>
        <CardDescription>
          Track the actual outcome of this capsule to improve future predictions
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Predicted Outcome (if available) */}
          {predictedOutcome && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <Label className="text-sm font-medium text-blue-900">
                Predicted Outcome
              </Label>
              <p className="text-sm text-blue-700 mt-1">{predictedOutcome}</p>
            </div>
          )}

          {/* Actual Outcome */}
          <div className="space-y-2">
            <Label htmlFor="actual-outcome" className="text-sm font-medium">
              Actual Outcome <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="actual-outcome"
              placeholder="Describe what actually happened..."
              value={actualOutcome}
              onChange={(e) => setActualOutcome(e.target.value)}
              rows={4}
              required
              className="resize-none"
            />
            <p className="text-xs text-gray-500">
              Describe the real-world result after this capsule was created
            </p>
          </div>

          {/* Quality Score */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="quality-score" className="text-sm font-medium">
                Outcome Quality Score
              </Label>
              <span className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                {qualityScore[0].toFixed(2)}
              </span>
            </div>
            <Slider
              id="quality-score"
              min={0}
              max={1}
              step={0.05}
              value={qualityScore}
              onValueChange={setQualityScore}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>0.0 (Failed)</span>
              <span>0.5 (Partial)</span>
              <span>1.0 (Perfect)</span>
            </div>
            <p className="text-xs text-gray-500">
              Rate how well the capsule's reasoning led to a successful outcome
            </p>
          </div>

          {/* Validation Method */}
          <div className="space-y-2">
            <Label htmlFor="validation-method" className="text-sm font-medium">
              Validation Method
            </Label>
            <Select value={validationMethod} onValueChange={setValidationMethod}>
              <SelectTrigger id="validation-method">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="user_feedback">User Feedback</SelectItem>
                <SelectItem value="automated_test">Automated Test</SelectItem>
                <SelectItem value="system_metric">System Metric</SelectItem>
                <SelectItem value="peer_review">Peer Review</SelectItem>
                <SelectItem value="production_monitoring">Production Monitoring</SelectItem>
                <SelectItem value="manual_verification">Manual Verification</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-gray-500">
              How was this outcome verified?
            </p>
          </div>

          {/* Validator ID (optional) */}
          <div className="space-y-2">
            <Label htmlFor="validator-id" className="text-sm font-medium">
              Validator ID <span className="text-gray-400">(optional)</span>
            </Label>
            <Input
              id="validator-id"
              placeholder="user_123, test_suite_v2, monitoring_system, etc."
              value={validatorId}
              onChange={(e) => setValidatorId(e.target.value)}
            />
            <p className="text-xs text-gray-500">
              Identifier for who or what validated this outcome
            </p>
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes" className="text-sm font-medium">
              Notes <span className="text-gray-400">(optional)</span>
            </Label>
            <Textarea
              id="notes"
              placeholder="Additional context, observations, or details..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="resize-none"
            />
          </div>

          {/* Status Messages */}
          {submitStatus === "success" && (
            <Alert className="bg-green-50 border-green-200">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                Outcome recorded successfully! This data will improve future predictions.
              </AlertDescription>
            </Alert>
          )}

          {submitStatus === "error" && (
            <Alert className="bg-red-50 border-red-200">
              <XCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                {errorMessage || "Failed to record outcome. Please try again."}
              </AlertDescription>
            </Alert>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button
              type="submit"
              disabled={isSubmitting}
              className="flex-1"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Recording...
                </>
              ) : (
                "Record Outcome"
              )}
            </Button>
            {onCancel && (
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
