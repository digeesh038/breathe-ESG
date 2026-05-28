// API payload shapes (mirroring the DRF serializers), expressed as JSDoc
// typedefs. With no TypeScript, this keeps editor autocomplete and documents
// the contract the React app codes against. Import-only; no runtime exports.

/** @typedef {"sap"|"utility"|"travel"} SourceType */
/** @typedef {"1"|"2"|"3"} Scope */
/** @typedef {"pending"|"approved"|"rejected"|"locked"} ReviewStatus */
/** @typedef {"outlier"|"missing_factor"|"unmapped_code"|"duplicate"|"unit_guess"} AnomalyKind */

/**
 * @typedef {Object} SourceConnection
 * @property {number} id
 * @property {string} name
 * @property {SourceType} source_type
 * @property {Object} config
 */

/**
 * @typedef {Object} IngestionBatch
 * @property {number} id
 * @property {number} source
 * @property {"received"|"parsing"|"normalized"|"failed"} status
 * @property {string} original_filename
 * @property {string} received_at
 * @property {number} row_count
 * @property {number} error_count
 */

/**
 * @typedef {Object} RawRecord
 * @property {number} id
 * @property {number} batch
 * @property {number} row_number
 * @property {Object} payload
 * @property {"pending"|"normalized"|"failed"} status
 * @property {string} error
 */

/**
 * @typedef {Object} ActivityRecord
 * @property {number} id
 * @property {number} batch
 * @property {string} activity_category
 * @property {Scope} scope
 * @property {string} site_code
 * @property {string} activity_date
 * @property {string} unit
 * @property {string} original_quantity
 * @property {string} quantity
 * @property {boolean} is_edited
 * @property {string|null} co2e_kg
 */

/**
 * @typedef {Object} AnomalyFlag
 * @property {number} id
 * @property {AnomalyKind} kind
 * @property {string} detail
 * @property {boolean} resolved
 */

/**
 * @typedef {Object} ReviewItem
 * @property {number} id
 * @property {number} activity
 * @property {ReviewStatus} status
 * @property {string} comment
 * @property {AnomalyFlag[]} flags
 */

export {};
