-- ============================================================================
-- 99_foreign_keys.sql - Contraintes d'intégrité référentielle
-- ============================================================================
-- Toutes les clés étrangères en un seul fichier
-- Exécuté en dernier après création de toutes les tables
--
-- Organisation par table source
-- ============================================================================

-- ============================================================================
-- action_subcategory
-- ============================================================================

ALTER TABLE public.action_subcategory
ADD CONSTRAINT action_subcategory_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.action_category (id);

-- ============================================================================
-- intervention
-- ============================================================================

ALTER TABLE public.intervention
ADD CONSTRAINT intervention_machine_id_fkey FOREIGN KEY (machine_id) REFERENCES public.machine (id);

ALTER TABLE public.intervention
ADD CONSTRAINT intervention_status_actual_foreign FOREIGN KEY (status_actual) REFERENCES public.intervention_status_ref (id);

-- ============================================================================
-- intervention_action
-- ============================================================================

ALTER TABLE public.intervention_action
ADD CONSTRAINT intervention_action_intervention_id_fkey FOREIGN KEY (intervention_id) REFERENCES public.intervention (id);

ALTER TABLE public.intervention_action
ADD CONSTRAINT intervention_action_action_subcategory_foreign FOREIGN KEY (action_subcategory) REFERENCES public.action_subcategory (id);

-- ============================================================================
-- intervention_part
-- ============================================================================

ALTER TABLE public.intervention_part
ADD CONSTRAINT intervention_part_intervention_id_fkey FOREIGN KEY (intervention_id) REFERENCES public.intervention (id);

-- ============================================================================
-- intervention_status_log
-- ============================================================================

ALTER TABLE public.intervention_status_log
ADD CONSTRAINT intervention_status_log_intervention_id_foreign FOREIGN KEY (intervention_id) REFERENCES public.intervention (id);

ALTER TABLE public.intervention_status_log
ADD CONSTRAINT intervention_status_log_status_from_foreign FOREIGN KEY (status_from) REFERENCES public.intervention_status_ref (id);

ALTER TABLE public.intervention_status_log
ADD CONSTRAINT intervention_status_log_status_to_foreign FOREIGN KEY (status_to) REFERENCES public.intervention_status_ref (id);

-- ============================================================================
-- machine
-- ============================================================================

ALTER TABLE public.machine
ADD CONSTRAINT machine_equipement_mere_foreign FOREIGN KEY (equipement_mere) REFERENCES public.machine (id);

ALTER TABLE public.machine
ADD CONSTRAINT machine_equipment_class_id_fkey FOREIGN KEY (equipment_class_id) REFERENCES public.equipment_class (id);

-- ============================================================================
-- purchase_request
-- ============================================================================

ALTER TABLE public.purchase_request
ADD CONSTRAINT purchase_request_stock_item_id_fkey FOREIGN KEY (stock_item_id) REFERENCES public.stock_item (id);

ALTER TABLE public.purchase_request
ADD CONSTRAINT purchase_request_intervention_id_foreign FOREIGN KEY (intervention_id) REFERENCES public.intervention (id);

-- ============================================================================
-- stock_item
-- ============================================================================

ALTER TABLE public.stock_item
ADD CONSTRAINT stock_item_family_code_fkey FOREIGN KEY (family_code) REFERENCES public.stock_family (code);

ALTER TABLE public.stock_item
ADD CONSTRAINT fk_item_sub_family FOREIGN KEY (family_code, sub_family_code) REFERENCES public.stock_sub_family (family_code, code);

ALTER TABLE public.stock_item
ADD CONSTRAINT stock_item_manufacturer_item_id_foreign FOREIGN KEY (manufacturer_item_id) REFERENCES public.manufacturer_item (id);

ALTER TABLE public.stock_item
ADD CONSTRAINT stock_item_standars_spec_foreign FOREIGN KEY (standars_spec) REFERENCES public.stock_item_standard_spec (id);

-- ============================================================================
-- stock_item_standard_spec
-- ============================================================================

ALTER TABLE public.stock_item_standard_spec
ADD CONSTRAINT stock_item_standard_spec_stock_item_id_foreign FOREIGN KEY (stock_item_id) REFERENCES public.stock_item (id);

-- ============================================================================
-- stock_item_supplier
-- ============================================================================

ALTER TABLE public.stock_item_supplier
ADD CONSTRAINT stock_item_supplier_stock_item_id_fkey FOREIGN KEY (stock_item_id) REFERENCES public.stock_item (id);

ALTER TABLE public.stock_item_supplier
ADD CONSTRAINT stock_item_supplier_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.supplier (id);

ALTER TABLE public.stock_item_supplier
ADD CONSTRAINT stock_item_supplier_manufacturer_item_id_fkey FOREIGN KEY (manufacturer_item_id) REFERENCES public.manufacturer_item (id) ON DELETE SET NULL;

-- ============================================================================
-- stock_sub_family
-- ============================================================================

ALTER TABLE public.stock_sub_family
ADD CONSTRAINT stock_sub_family_family_code_fkey FOREIGN KEY (family_code) REFERENCES public.stock_family (code);

-- ============================================================================
-- subtask
-- ============================================================================

ALTER TABLE public.subtask
ADD CONSTRAINT subtask_intervention_id_fkey FOREIGN KEY (intervention_id) REFERENCES public.intervention (id);

-- ============================================================================
-- supplier_order
-- ============================================================================

ALTER TABLE public.supplier_order
ADD CONSTRAINT supplier_order_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.supplier (id);

-- ============================================================================
-- supplier_order_line
-- ============================================================================

ALTER TABLE public.supplier_order_line
ADD CONSTRAINT supplier_order_line_supplier_order_id_fkey FOREIGN KEY (supplier_order_id) REFERENCES public.supplier_order (id);

ALTER TABLE public.supplier_order_line
ADD CONSTRAINT supplier_order_line_stock_item_id_fkey FOREIGN KEY (stock_item_id) REFERENCES public.stock_item (id);

-- ============================================================================
-- supplier_order_line_purchase_request
-- ============================================================================

ALTER TABLE public.supplier_order_line_purchase_request
ADD CONSTRAINT supplier_order_line_purchase_reques_supplier_order_line_id_fkey FOREIGN KEY (supplier_order_line_id) REFERENCES public.supplier_order_line (id);

ALTER TABLE public.supplier_order_line_purchase_request
ADD CONSTRAINT supplier_order_line_purchase_request_purchase_request_id_fkey FOREIGN KEY (purchase_request_id) REFERENCES public.purchase_request (id);

-- ============================================================================
-- action_category_meta
-- ============================================================================
-- Notes:
-- - action_category_meta.category_code et action_classification_probe.suggested_category
--   ne référencent pas action_category car la structure utilise des codes VARCHAR
--   au lieu d'une FK sur l'ID. Ces contraintes n'existent pas en base.
-- ============================================================================