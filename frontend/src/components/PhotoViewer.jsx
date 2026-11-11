import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

// Full-size view of an animal photo on top of the page. Closes with the
// close button, the Escape key or a click on the dark background.
// Rendered into <body> so the card's overflow: hidden can't cut it off.
export function PhotoViewer({ src, alt, onClose }) {
  const closeRef = useRef(null);

  useEffect(() => {
    function handleKey(event) {
      if (event.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', handleKey);
    closeRef.current?.focus();
    // Stop the page behind from scrolling while the photo is open.
    const oldOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.body.style.overflow = oldOverflow;
    };
  }, [onClose]);

  return createPortal(
    <div className="photo-viewer" role="dialog" aria-modal="true" aria-label={alt} onClick={onClose}>
      <button
        type="button"
        ref={closeRef}
        className="photo-viewer-close"
        onClick={onClose}
        aria-label="Close photo"
      >
        ×
      </button>
      <img
        src={src}
        alt={alt}
        className="photo-viewer-image"
        onClick={(event) => event.stopPropagation()}
      />
    </div>,
    document.body,
  );
}
