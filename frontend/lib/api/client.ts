/* =========================================================
   SHARED API CLIENT
=========================================================

Single HTTP client for the frontend.

Responsibilities
----------------
- API base URL
- JSON request handling
- credentials
- response parsing
- consistent API errors
- network error handling

Domain-specific APIs should live in:
    lib/api/workflowApi.ts
    lib/api/processingApi.ts
    lib/api/documentApi.ts
    etc.

========================================================= */

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000/api/v1'
).replace(/\/+$/, '');


/* =========================================================
   API ERROR
========================================================= */

export class ApiError extends Error {
  readonly status: number;

  readonly responseBody: unknown;

  readonly url: string;

  readonly method: string;

  constructor(
    message: string,
    status: number,
    responseBody?: unknown,
    url = '',
    method = 'GET',
  ) {
    super(message);

    this.name = 'ApiError';

    this.status = status;

    this.responseBody =
      responseBody ?? null;

    this.url = url;

    this.method = method;

    Object.setPrototypeOf(
      this,
      ApiError.prototype,
    );
  }
}


/* =========================================================
   API BASE URL
========================================================= */

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}


/* =========================================================
   RESPONSE MESSAGE EXTRACTION
========================================================= */

function getErrorMessage(
  status: number,
  responseBody: unknown,
): string {
  let message =
    `API request failed with status ${status}.`;

  if (
    typeof responseBody === 'object' &&
    responseBody !== null
  ) {
    const body =
      responseBody as Record<
        string,
        unknown
      >;

    if (
      typeof body.detail === 'string' &&
      body.detail.trim()
    ) {
      message = body.detail;
    } else if (
      Array.isArray(body.detail)
    ) {
      message =
        `API validation failed with status ${status}.`;
    } else if (
      typeof body.message === 'string' &&
      body.message.trim()
    ) {
      message = body.message;
    } else if (
      typeof body.error === 'string' &&
      body.error.trim()
    ) {
      message = body.error;
    }
  } else if (
    typeof responseBody === 'string' &&
    responseBody.trim()
  ) {
    message =
      responseBody;
  }

  return message;
}


/* =========================================================
   GENERIC REQUEST
========================================================= */

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const normalizedPath =
    path.startsWith('/')
      ? path
      : `/${path}`;

  const url =
    `${API_BASE_URL}${normalizedPath}`;

  const method =
    options.method || 'GET';

  const headers =
    new Headers(options.headers);

  /*
   * Automatically use JSON when a body exists,
   * unless the caller explicitly supplied a
   * Content-Type or is uploading FormData.
   */
  if (
    options.body !== undefined &&
    !(options.body instanceof FormData) &&
    !headers.has('Content-Type')
  ) {
    headers.set(
      'Content-Type',
      'application/json',
    );
  }

  let response: Response;

  try {
    response = await fetch(
      url,
      {
        ...options,
        headers,
        credentials: 'include',
      },
    );
  } catch (error: unknown) {
    const message =
      error instanceof Error
        ? error.message
        : 'Network request failed.';

    console.error(
      '[API NETWORK ERROR]',
      {
        method,
        url,
        error,
      },
    );

    throw new ApiError(
      message,
      0,
      null,
      url,
      method,
    );
  }

  /*
   * 204 No Content.
   */
  if (response.status === 204) {
    return undefined as T;
  }

  /*
   * Safely parse the response.
   */
  const contentType =
    response.headers.get(
      'content-type',
    ) || '';

  let responseBody: unknown = null;

  if (
    contentType.includes(
      'application/json',
    )
  ) {
    try {
      responseBody =
        await response.json();
    } catch {
      responseBody = null;
    }
  } else {
    try {
      responseBody =
        await response.text();
    } catch {
      responseBody = null;
    }
  }

  /*
   * Every non-2xx response becomes
   * a typed ApiError.
   */
  if (!response.ok) {
    const message =
      getErrorMessage(
        response.status,
        responseBody,
      );

    console.error(
      '[API ERROR]',
      {
        method,
        url,
        status: response.status,
        statusText: response.statusText,
        responseBody,
      },
    );

    throw new ApiError(
      message,
      response.status,
      responseBody,
      url,
      method,
    );
  }

  return responseBody as T;
}


/* =========================================================
   OPTIONAL JSON HELPERS
========================================================= */

export function jsonBody(
  value: unknown,
): string {
  return JSON.stringify(value);
}


/* =========================================================
   PUBLIC EXPORTS
========================================================= */

export {
  API_BASE_URL,
};