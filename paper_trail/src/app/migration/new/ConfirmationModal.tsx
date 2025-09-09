// src/app/migration/new/ConfirmationModal.tsx
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { CheckIcon as Check, PencilIcon as Edit, XMarkIcon as X } from '@heroicons/react/24/outline';

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  context: {
    originCountry: string;
    destinationCountry: string;
    purpose: string;
  };
}

export default function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  context,
}: ConfirmationModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center"
        >
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8"
          >
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Confirm Your Plan</h2>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
            <p className="text-gray-600 mb-6">
              Our AI has detected the following details from your query. Does this look correct?
            </p>
            <div className="space-y-4 text-lg">
              <div className="flex items-center">
                <span className="font-semibold w-40">From:</span>
                <span className="text-gray-800">{context.originCountry}</span>
              </div>
              <div className="flex items-center">
                <span className="font-semibold w-40">To:</span>
                <span className="text-gray-800">{context.destinationCountry}</span>
              </div>
              <div className="flex items-center">
                <span className="font-semibold w-40">Purpose:</span>
                <span className="text-gray-800 capitalize">{context.purpose}</span>
              </div>
            </div>
            <div className="flex justify-end space-x-4 mt-8">
              <button
                onClick={onClose}
                className="border border-gray-300 hover:border-gray-400 text-gray-700 px-6 py-2 rounded-lg font-medium transition flex items-center space-x-2"
              >
                <Edit className="w-4 h-4" />
                <span>Edit Manually</span>
              </button>
              <button
                onClick={onConfirm}
                className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg font-medium transition flex items-center space-x-2"
              >
                <Check className="w-4 h-4" />
                <span>Yes, looks right!</span>
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
