

## 🎯 CONTEXTE ET OBJECTIF GÉNÉRAL

Tu es un expert en développement Odoo 18. On te demande de modifier un **module Odoo 18 complet et professionnel** permettant la **personnalisation dynamique des modèles de rapport (template PDF) pour les factures**, avec un système intelligent de **sélection basée sur le type de facture** choisi par l'utilisateur via un **dialog popup au moment de la création de la facture**.

---

## 📋 SPÉCIFICATIONS FONCTIONNELLES DÉTAILLÉES - RÉVISÉES

### **1. TYPES DE FACTURES ET LEURS CAS D'USAGE - VERSION CORRIGÉE**

#### **CAS A : FACTURE SIMPLE/NORMALE**

**Condition d'application** :
- Utilisateur sélectionne "Facture Normale" dans le popup de création
- Peut être avec ou sans Sale Order (SO)
- **Cas A1** : Aucun acompte précédent sur cette SO/Devis → **Template** : `simple_invoice_1.pdf`
- **Cas A2** : Il y avait des acomptes précédents, mais c'est la facture finale qui complète → **Template** : `final_invoice.pdf`

**Détail A1 - Simple Invoice** :
- Affiche les articles
- Affiche montant HT, TVA, montant NET A PAYER
- Pas de section "ACOMPTES"
- Exemple : Facture FAC/2026/00039

**Détail A2 - Final Invoice** :
- Affiche les articles
- Affiche une section "ACOMPTES" listant TOUS les acomptes payés précédemment
- Affiche : TOTAL ACOMPTES PAYÉS + SOLDE HT + TVA + MONTANT NET A PAYER
- Exemple : Facture FAC/2026/00070 (facture solde après 3 acomptes)

---

#### **CAS B : FACTURE D'ACOMPTE**

**Condition d'application** :
- Utilisateur sélectionne "Facture d'Acompte" dans le popup de création
- Peut être avec ou sans Sale Order (SO)

**Cas B1 - Première Acompte** :
- C'est le 1er acompte sur cette SO/Devis
- **Template** : `first_down_payment_invoice_1.pdf`
- Affiche les articles
- Affiche "Acompte n°1 à payer [pourcentage]%"
- Affiche montant acompte HT, TVA, NET A PAYER
- Affiche "RESTE A PAYER"
- Exemple : Facture FAC/2026/00070 (20% = 720 000 CFA)

**Cas B2 - Acomptes Suivants (2ème, 3ème, 4ème...)** :
- C'est le 2ème, 3ème, 4ème... acompte sur cette SO/Devis
- **Template** : `2nd_down_payment_invoice_1.pdf` / `3rd_down_payment_invoice_1.pdf` / etc.
- Affiche les articles
- Affiche la section "ACOMPTES" : tous les acomptes payés précédemment
- Affiche "TOTAL DES ACOMPTES PAYÉS"
- Affiche "Acompte n°X à payer [pourcentage]%"
- Affiche montant acompte HT, TVA, NET A PAYER
- Affiche "RESTE A PAYER"
- Exemples :
  - FAC/2026/00080 (2nd acompte - 30%)
  - FAC/2026/00095 (3rd acompte - 15%)

---

### **2. POPUP DE SÉLECTION - POINT CLEF**

#### **2.1 MOMENT D'ACTIVATION**

**Quand afficher le popup** :
1. Utilisateur clique sur "Créer une Facture" depuis une Sale Order
2. OU Utilisateur crée manuellement une facture (account.move avec move_type='out_invoice')
3. OU Utilisateur change le type de facture d'une facture brouillon

**Actions du popup** :
```
┌─────────────────────────────────────────┐
│  TYPE DE FACTURE                        │
├─────────────────────────────────────────┤
│                                         │
│  ☐ Facture Normale/Simple               │
│  ☐ Facture d'Acompte                    │
│                                         │
│  [CONFIRMER]  [ANNULER]                 │
│                                         │
└─────────────────────────────────────────┘
```

#### **2.2 DÉTERMINISME DU POPUP**

**Logique à implémenter** :

```python
# Dans le modèle account.move - Événement onchange ou button_create

def _show_invoice_type_dialog(self):
    """Afficher le dialog de sélection du type de facture"""
    return {
        'type': 'ir.actions.act_window',
        'res_model': 'account.move.invoice.type.wizard',
        'view_mode': 'form',
        'target': 'new',
        'context': {
            'default_move_id': self.id,
            'default_sale_order_id': self.sale_order_id.id if self.sale_order_id else False,
        }
    }
```

---

## 🔧 SPÉCIFICATIONS TECHNIQUES DÉTAILLÉES - RÉVISÉES

### **3. DÉTECTION AUTOMATIQUE DU TEMPLATE**

#### **3.1 ALGORITHME DE SÉLECTION DU TEMPLATE (RÉVISÉ)**

```
ÉTAPE 1 : Utilisateur sélectionne type via POPUP
  └─ 'facture_normale' OU 'facture_acompte'

ÉTAPE 2 : Si type == 'facture_normale'
  ├─ Chercher les acomptes payés liés (même SO/Devis)
  ├─ Si count(acomptes payés) == 0 :
  │   └─ Template = "simple_invoice_1"
  └─ Sinon (count > 0) :
      └─ Template = "final_invoice"

ÉTAPE 3 : Si type == 'facture_acompte'
  ├─ Chercher les acomptes payés précédemment (même SO/Devis)
  ├─ Si count(acomptes payés) == 0 :
  │   ├─ downpayment_sequence_number = 1
  │   └─ Template = "first_down_payment_invoice_1"
  └─ Sinon (count > 0) :
      ├─ downpayment_sequence_number = count + 1
      └─ Template = "2nd_down_payment_invoice_1" / "3rd_..." / etc.
```

#### **3.2 CRITÈRES DE SÉLECTION (SIMPLIFIÉ)**

**Champs clefs** :

```python
# Dans account.move

invoice_type = fields.Selection([
    ('normal', 'Facture Normale/Simple'),
    ('downpayment', 'Facture d\'Acompte')
], string='Invoice Type', required=True, default='normal',
   help='Sélectionné manuellement via popup')

downpayment_sequence_number = fields.Integer(
    string='Down Payment Sequence Number',
    default=0,
    help='0 si facture normale, 1+ si acompte'
)

custom_report_template = fields.Selection(
    ..., compute='_compute_custom_report_template', store=True
)

# Ces champs se calculent automatiquement après sélection du type
```

---

### **4. STRUCTURE DU MODULE ODOO 18 - RÉVISÉE**

#### **4.1 ARBORESCENCE COMPLÈTE**

```
account_invoice_report_customizer/
│
├── __init__.py
├── __manifest__.py
│
├── models/
│   ├── __init__.py
│   ├── account_move_extension.py         # Extension account.move
│   ├── invoice_type_wizard.py            # Wizard du popup
│   └── report_template_config.py         # Config templates (optionnel)
│
├── views/
│   ├── __init__.py
│   ├── account_move_views.xml            # Ajout champs + logique popup
│   ├── invoice_type_wizard_views.xml     # Vue du dialog popup
│   └── report_template_config_views.xml  # (optionnel)
│
├── reports/
│   ├── __init__.py
│   ├── invoice_report.xml                # Définition rapport principal
│   └── templates/
│       ├── simple_invoice_1.xml
│       ├── final_invoice.xml
│       ├── first_down_payment_invoice_1.xml
│       ├── 2nd_down_payment_invoice_1.xml
│       └── 3rd_down_payment_invoice_1.xml
│
├── static/
│   ├── description/
│   │   └── icon.png
│   └── pdfs/                             # PDFs de référence
│       ├── simple_invoice_1.pdf
│       ├── final_invoice.pdf
│       ├── first_down_payment_invoice_1.pdf
│       ├── 2nd_down_payment_invoice_1.pdf
│       └── 3rd_down_payment_invoice_1.pdf
│
└── security/
    └── ir.model.access.csv
```

---

### **5. MODÈLES DE DONNÉES - VERSION RÉVISÉE**

#### **5.1 EXTENSION account.move**

```python
# models/account_move_extension.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # ============ CHAMPS PRINCIPAUX ============
    
    # Type de facture - Sélectionné manuellement via popup
    invoice_type = fields.Selection([
        ('normal', 'Facture Normale/Simple'),
        ('downpayment', 'Facture d\'Acompte')
    ], string='Invoice Type', 
       default='normal',
       help='Type de facture choisi lors de la création')
    
    # Numéro de séquence pour acompte (1=1er, 2=2ème, etc.)
    downpayment_sequence_number = fields.Integer(
        string='Down Payment Sequence Number',
        default=0,
        help='0 si facture normale, 1+ si acompte'
    )
    
    # ============ CHAMPS CALCULÉS ============
    
    # Nombre d'acomptes payés AVANT celui-ci
    previous_downpayments_count = fields.Integer(
        string='Previous Down Payments Count',
        compute='_compute_previous_downpayments_count'
    )
    
    # Montant total des acomptes déjà payés
    total_downpayments_paid = fields.Monetary(
        string='Total Down Payments Paid',
        compute='_compute_total_downpayments_paid'
    )
    
    # Déterminer si c'est le dernier paiement
    is_final_payment = fields.Boolean(
        string='Is Final Payment',
        compute='_compute_is_final_payment'
    )
    
    # Template à utiliser (calculé automatiquement)
    custom_report_template = fields.Selection([
        ('simple_invoice_1', 'Simple Invoice 1'),
        ('final_invoice', 'Final Invoice'),
        ('first_down_payment_invoice_1', 'First Down Payment Invoice 1'),
        ('2nd_down_payment_invoice_1', '2nd Down Payment Invoice 1'),
        ('3rd_down_payment_invoice_1', '3rd Down Payment Invoice 1'),
        ('4th_down_payment_invoice_1', '4th Down Payment Invoice 1'),
        ('5th_down_payment_invoice_1', '5th Down Payment Invoice 1'),
    ], string='Custom Report Template',
       compute='_compute_custom_report_template',
       store=True
    )
    
    # ============ MÉTHODES DE CALCUL ============
    
    @api.depends('invoice_type', 'downpayment_sequence_number', 'is_final_payment')
    def _compute_custom_report_template(self):
        """Sélectionner automatiquement le template"""
        for record in self:
            if record.invoice_type == 'normal':
                # Facture normale : simple ou finale ?
                if record.previous_downpayments_count > 0:
                    record.custom_report_template = 'final_invoice'
                else:
                    record.custom_report_template = 'simple_invoice_1'
            
            elif record.invoice_type == 'downpayment':
                # Facture acompte : numéroter
                if record.downpayment_sequence_number == 1:
                    record.custom_report_template = 'first_down_payment_invoice_1'
                else:
                    seq = record.downpayment_sequence_number
                    ordinal = self._get_ordinal_number(seq)
                    record.custom_report_template = f'{ordinal}_down_payment_invoice_1'
            else:
                record.custom_report_template = 'simple_invoice_1'
    
    @api.depends('sale_order_id', 'state', 'create_date')
    def _compute_previous_downpayments_count(self):
        """Compter les acomptes payés AVANT celui-ci"""
        for record in self:
            # Chercher sur la SO ou le devis source
            source_ref = record.sale_order_id or (
                record.invoice_origin and 
                self.env['sale.order'].search(
                    [('name', '=', record.invoice_origin)], limit=1
                )
            )
            
            if source_ref:
                count = self.search_count([
                    ('sale_order_id', '=', source_ref.id),
                    ('invoice_type', '=', 'downpayment'),
                    ('state', '=', 'posted'),
                    ('create_date', '<', record.create_date or '9999-12-31')
                ])
                record.previous_downpayments_count = count
            else:
                record.previous_downpayments_count = 0
    
    @api.depends('sale_order_id', 'state', 'create_date')
    def _compute_total_downpayments_paid(self):
        """Calculer le montant total des acomptes payés"""
        for record in self:
            source_ref = record.sale_order_id or (
                record.invoice_origin and 
                self.env['sale.order'].search(
                    [('name', '=', record.invoice_origin)], limit=1
                )
            )
            
            if source_ref:
                downpayment_invoices = self.search([
                    ('sale_order_id', '=', source_ref.id),
                    ('invoice_type', '=', 'downpayment'),
                    ('state', '=', 'posted'),
                    ('id', '!=', record.id),
                    ('create_date', '<', record.create_date or '9999-12-31')
                ])
                record.total_downpayments_paid = sum(
                    inv.amount_total for inv in downpayment_invoices
                )
            else:
                record.total_downpayments_paid = 0
    
    @api.depends('sale_order_id', 'amount_total', 'total_downpayments_paid')
    def _compute_is_final_payment(self):
        """Vérifier si c'est le dernier paiement (complète la SO)"""
        for record in self:
            source_ref = record.sale_order_id or (
                record.invoice_origin and 
                self.env['sale.order'].search(
                    [('name', '=', record.invoice_origin)], limit=1
                )
            )
            
            if source_ref:
                total_so = source_ref.amount_total
                already_paid = record.total_downpayments_paid
                current_amount = record.amount_untaxed  # HT
                
                # Vérifier si le total atteint le montant de la SO
                record.is_final_payment = (
                    abs((already_paid + current_amount) - total_so) < 0.01
                )
            else:
                record.is_final_payment = False
    
    # ============ MÉTHODES UTILITAIRES ============
    
    @staticmethod
    def _get_ordinal_number(num):
        """Retourner 2nd, 3rd, 4th, etc."""
        if num == 2:
            return '2nd'
        elif num == 3:
            return '3rd'
        elif num == 4:
            return '4th'
        else:
            return f'{num}th'
    
    def _get_previous_downpayments(self):
        """Retourner les détails de tous les acomptes précédents"""
        self.ensure_one()
        
        source_ref = self.sale_order_id or (
            self.invoice_origin and 
            self.env['sale.order'].search(
                [('name', '=', self.invoice_origin)], limit=1
            )
        )
        
        if not source_ref:
            return []
        
        downpayments = self.search([
            ('sale_order_id', '=', source_ref.id),
            ('invoice_type', '=', 'downpayment'),
            ('state', '=', 'posted'),
            ('create_date', '<', self.create_date)
        ], order='create_date asc')
        
        result = []
        for idx, dp in enumerate(downpayments, 1):
            result.append({
                'sequence': idx,
                'invoice_name': dp.name,
                'invoice_date': dp.invoice_date.strftime('%d/%m/%Y') if dp.invoice_date else '',
                'amount_total': dp.amount_total,
                'amount_untaxed': dp.amount_untaxed,
            })
        return result
    
    # ============ ACTIONS - POPUP DIALOG ============
    
    def action_show_invoice_type_dialog(self):
        """Afficher le dialog de sélection du type de facture"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.invoice.type.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
                'default_sale_order_id': self.sale_order_id.id if self.sale_order_id else False,
            }
        }
    
    @api.onchange('invoice_type')
    def _onchange_invoice_type(self):
        """Mettre à jour les champs calculés quand le type change"""
        if self.invoice_type == 'normal':
            self.downpayment_sequence_number = 0
        elif self.invoice_type == 'downpayment':
            # Calculer le numéro de séquence automatiquement
            self.downpayment_sequence_number = self.previous_downpayments_count + 1
```

---

#### **5.2 WIZARD - POPUP DE SÉLECTION**

```python
# models/invoice_type_wizard.py

from odoo import models, fields, api, _

class InvoiceTypeWizard(models.TransientModel):
    _name = 'account.move.invoice.type.wizard'
    _description = 'Invoice Type Selection Dialog'
    
    move_id = fields.Many2one('account.move', string='Invoice', required=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    
    invoice_type = fields.Selection([
        ('normal', 'Facture Normale/Simple'),
        ('downpayment', 'Facture d\'Acompte')
    ], string='Type de Facture', required=True, default='normal')
    
    # Texte informatif
    message = fields.Html(
        string='Information',
        compute='_compute_message'
    )
    
    @api.depends('sale_order_id', 'move_id')
    def _compute_message(self):
        """Afficher le contexte (acomptes existants, etc.)"""
        for record in self:
            so = record.sale_order_id or (
                record.move_id.sale_order_id
            )
            
            message = "<h4>Sélectionnez le type de facture :</h4>"
            message += "<ul>"
            message += "<li><b>Facture Normale</b> : Facture complète ou facture solde</li>"
            message += "<li><b>Facture d'Acompte</b> : Paiement partiel</li>"
            message += "</ul>"
            
            if so:
                # Compter les acomptes existants
                existing_downpayments = self.env['account.move'].search_count([
                    ('sale_order_id', '=', so.id),
                    ('invoice_type', '=', 'downpayment'),
                    ('state', '=', 'posted'),
                ])
                
                if existing_downpayments > 0:
                    message += f"<br/><p style='color:blue;'>"
                    message += f"⚠️ {existing_downpayments} acompte(s) déjà payé(s) sur cette commande."
                    message += f"</p>"
            
            record.message = message
    
    def action_confirm(self):
        """Confirmer le type de facture et fermer le dialog"""
        self.ensure_one()
        
        # Mettre à jour la facture
        self.move_id.invoice_type = self.invoice_type
        
        # Calculer le numéro de séquence si acompte
        if self.invoice_type == 'downpayment':
            so = self.move_id.sale_order_id or (
                self.move_id.invoice_origin and 
                self.env['sale.order'].search(
                    [('name', '=', self.move_id.invoice_origin)], limit=1
                )
            )
            
            if so:
                existing_count = self.env['account.move'].search_count([
                    ('sale_order_id', '=', so.id),
                    ('invoice_type', '=', 'downpayment'),
                    ('state', '=', 'posted'),
                ])
                self.move_id.downpayment_sequence_number = existing_count + 1
        
        # Forcer le recalcul des champs calculés
        self.move_id._compute_custom_report_template()
        self.move_id._compute_previous_downpayments_count()
        self.move_id._compute_total_downpayments_paid()
        
        return {'type': 'ir.actions.act_window_close'}
```

---

### **6. VIEWS - INTERFACE UTILISATEUR**

#### **6.1 Vue du Wizard (Popup Dialog)**

```xml
<!-- views/invoice_type_wizard_views.xml -->

<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        <!-- Form view du wizard -->
        <record id="invoice_type_wizard_form" model="ir.ui.view">
            <field name="name">Invoice Type Selection Dialog</field>
            <field name="model">account.move.invoice.type.wizard</field>
            <field name="arch" type="xml">
                <form>
                    <div class="alert alert-info" role="alert">
                        <t t-esc="record.message"/>
                    </div>
                    
                    <group>
                        <field name="move_id" invisible="1"/>
                        <field name="sale_order_id" invisible="1"/>
                        
                        <div>
                            <label for="invoice_type" class="font-weight-bold"/>
                            <br/>
                            <field name="invoice_type" widget="radio" 
                                   options="{'horizontal': true}"/>
                        </div>
                    </group>
                    
                    <footer>
                        <button name="action_confirm" type="object" 
                                string="Confirmer" class="btn-primary"/>
                        <button special="cancel" string="Annuler" 
                                class="btn-secondary"/>
                    </footer>
                </form>
            </field>
        </record>
    </data>
</odoo>
```

#### **6.2 Extension Vue account.move**

```xml
<!-- views/account_move_views.xml -->

<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        <!-- Extension de la vue form account.move -->
        <record id="invoice_form_custom" model="ir.ui.view">
            <field name="name">Invoice Form - Custom Fields</field>
            <field name="model">account.move</field>
            <field name="inherit_id" ref="account.move_form"/>
            <field name="arch" type="xml">
                
                <!-- Ajouter champs personnalisés dans la section invoice -->
                <xpath expr="//div[@class='oe_title']" position="after">
                    <group colspan="2">
                        <field name="invoice_type" readonly="1"/>
                        <field name="downpayment_sequence_number" readonly="1"/>
                        <field name="custom_report_template" invisible="1"/>
                    </group>
                </xpath>
                
                <!-- Ajouter button pour afficher le dialog -->
                <xpath expr="//button[@name='action_post']" position="before">
                    <button name="action_show_invoice_type_dialog" 
                            type="object" 
                            string="Sélectionner Type de Facture"
                            class="btn-info"
                            attrs="{'invisible': [('state', '!=', 'draft')]}"/>
                </xpath>
                
                <!-- Afficher les champs calculés en readonly -->
                <xpath expr="//group[@name='invoice_data']" position="inside">
                    <field name="previous_downpayments_count" readonly="1" 
                           attrs="{'invisible': [('invoice_type', '!=', 'downpayment')]}"/>
                    <field name="total_downpayments_paid" readonly="1"
                           attrs="{'invisible': [('previous_downpayments_count', '=', 0)]}"/>
                    <field name="is_final_payment" readonly="1"
                           attrs="{'invisible': [('invoice_type', '!=', 'normal')]}"/>
                </xpath>
                
            </field>
        </record>
        
        <!-- Vue tree personnalisée -->
        <record id="invoice_tree_custom" model="ir.ui.view">
            <field name="name">Invoice Tree - Custom Fields</field>
            <field name="model">account.move</field>
            <field name="inherit_id" ref="account.move_tree"/>
            <field name="arch" type="xml">
                <xpath expr="//field[@name='name']" position="after">
                    <field name="invoice_type"/>
                    <field name="custom_report_template" optional="hide"/>
                </xpath>
            </field>
        </record>
        
    </data>
</odoo>
```

---

### **7. TEMPLATES DE RAPPORT QWEB**

#### **7.1 Rapport Principal avec Sélection Dynamique**

```xml
<!-- reports/invoice_report.xml -->

<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        <!-- Rapport personnalisé -->
        <record id="invoice_custom_report" model="ir.actions.report">
            <field name="name">Custom Invoice Report</field>
            <field name="model">account.move</field>
            <field name="report_type">qweb-pdf</field>
            <field name="report_name">account_invoice_report_customizer.invoice_report_template</field>
            <field name="print_report_name">'Invoice - %s' % (object.name.replace('/', '_'))</field>
            <field name="binding_model_id" ref="account.model_account_move"/>
            <field name="binding_type">report</field>
        </record>

        <!-- Template principal - Sélection dynamique -->
        <template id="invoice_report_template">
            <t t-call="web.html_container">
                <t t-foreach="docs" t-as="doc">
                    <!-- Sélection basée sur custom_report_template -->
                    <t t-if="doc.custom_report_template == 'simple_invoice_1'">
                        <t t-call="account_invoice_report_customizer.simple_invoice_1_template"/>
                    </t>
                    <t t-elif="doc.custom_report_template == 'final_invoice'">
                        <t t-call="account_invoice_report_customizer.final_invoice_template"/>
                    </t>
                    <t t-elif="doc.custom_report_template == 'first_down_payment_invoice_1'">
                        <t t-call="account_invoice_report_customizer.first_down_payment_invoice_1_template"/>
                    </t>
                    <t t-elif="'down_payment_invoice' in (doc.custom_report_template or '')" t-if="doc.downpayment_sequence_number >= 2">
                        <t t-call="account_invoice_report_customizer.nth_down_payment_invoice_template"/>
                    </t>
                    <t t-else="">
                        <!-- Fallback : template Odoo par défaut -->
                        <t t-call="account.report_invoice"/>
                    </t>
                </t>
            </t>
        </template>

    </data>
</odoo>
```

#### **7.2 Template : Simple Invoice 1**

```xml
<!-- reports/templates/simple_invoice_1.xml -->

<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        <template id="simple_invoice_1_template">
            <t t-call="web.external_layout">
                <div class="page">
                    
                    <!-- HEADER -->
                    <div class="row mb-4">
                        <div class="col-7">
                            <img t-if="doc.company_id.logo" 
                                 t-att-src="image_data_uri(doc.company_id.logo)" 
                                 style="max-height: 100px;" alt="Logo"/>
                        </div>
                        <div class="col-5 text-right">
                            <h2 class="mt-4">FACTURE</h2>
                            <p class="mt-2"><strong t-field="doc.name"/></p>
                            <p><t t-esc="doc.invoice_date.strftime('%d/%m/%Y') if doc.invoice_date else ''"/></p>
                        </div>
                    </div>

                    <!-- INFOS DE ET DOIT -->
                    <div class="row mb-3">
                        <div class="col-6">
                            <strong>DE :</strong>
                            <p t-field="doc.company_id.name"/>
                            <p t-field="doc.company_id.street"/>
                        </div>
                        <div class="col-6">
                            <strong>DOIT :</strong>
                            <p t-field="doc.partner_id.name"/>
                            <p t-field="doc.partner_id.street"/>
                        </div>
                    </div>

                    <!-- OBJET -->
                    <div class="row mb-3">
                        <div class="col-12">
                            <strong>OBJET :</strong>
                            <p t-esc="doc.narration or ''"/>
                        </div>
                    </div>

                    <!-- TABLE DES ARTICLES -->
                    <div class="row mb-3">
                        <div class="col-12">
                            <table class="table table-sm">
                                <thead>
                                    <tr style="background-color: #e9ecef;">
                                        <th>Description</th>
                                        <th class="text-center">Quantité</th>
                                        <th class="text-center">Unité</th>
                                        <th class="text-right">Prix unitaire</th>
                                        <th class="text-right">Montant</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <t t-foreach="doc.invoice_line_ids" t-as="line">
                                        <t t-if="not line.display_type">
                                            <tr>
                                                <td><span t-esc="line.name"/></td>
                                                <td class="text-center">
                                                    <t t-esc="'{:,.0f}'.format(line.quantity)"/>
                                                </td>
                                                <td class="text-center">
                                                    <t t-esc="line.product_uom_id.name or ''"/>
                                                </td>
                                                <td class="text-right">
                                                    <t t-esc="'{:,.2f}'.format(line.price_unit)"/>
                                                </td>
                                                <td class="text-right">
                                                    <t t-esc="'{:,.2f}'.format(line.price_subtotal)"/>
                                                </td>
                                            </tr>
                                        </t>
                                    </t>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- TOTAUX -->
                    <div class="row">
                        <div class="col-6"/>
                        <div class="col-6">
                            <table class="table table-sm">
                                <tr>
                                    <td><strong>MONTANT HT</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(doc.amount_untaxed) + ' CFA'"/>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>TVA 18%</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(doc.amount_tax) + ' CFA'"/>
                                    </td>
                                </tr>
                                <tr style="background-color: #f0f0f0; font-weight: bold;">
                                    <td><strong>MONTANT NET A PAYER</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(doc.amount_total) + ' CFA'"/>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <!-- INFOS PAIEMENT -->
                    <div class="row mt-4">
                        <div class="col-12">
                            <p><strong>Communication de paiement :</strong> <t t-esc="doc.name"/></p>
                            <p t-if="doc.company_id.bank_ids">
                                <strong>Sur ce compte :</strong>
                                <t t-esc="doc.company_id.bank_ids[0].acc_number"/> - 
                                <t t-esc="doc.company_id.bank_ids[0].bank_id.name"/>
                            </p>
                        </div>
                    </div>

                    <!-- FOOTER -->
                    <div class="row mt-4 pt-2" style="border-top: 2px solid #ccc;">
                        <div class="col-12 text-center">
                            <p style="font-size: 10px; color: #666;">
                                Toute réclamation concernant la conformité des produits / services 
                                doit être formulée par écrit dans un délai de 15 jours suivant la réception de la facture
                            </p>
                        </div>
                    </div>

                </div>
            </t>
        </template>

    </data>
</odoo>
```

#### **7.3 Template : Final Invoice**

```xml
<!-- reports/templates/final_invoice.xml -->

<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        <template id="final_invoice_template">
            <t t-call="web.external_layout">
                <div class="page">
                    
                    <!-- HEADER -->
                    <div class="row mb-4">
                        <div class="col-7">
                            <img t-if="doc.company_id.logo" 
                                 t-att-src="image_data_uri(doc.company_id.logo)" 
                                 style="max-height: 100px;" alt="Logo"/>
                        </div>
                        <div class="col-5 text-right">
                            <h2 class="mt-4">FACTURE</h2>
                            <p class="mt-2"><strong t-field="doc.name"/></p>
                            <p><t t-esc="doc.invoice_date.strftime('%d/%m/%Y') if doc.invoice_date else ''"/></p>
                        </div>
                    </div>

                    <!-- INFOS CLIENT -->
                    <div class="row mb-3">
                        <div class="col-6">
                            <strong>DE :</strong>
                            <p t-field="doc.company_id.name"/>
                        </div>
                        <div class="col-6">
                            <strong>DOIT :</strong>
                            <p t-field="doc.partner_id.name"/>
                        </div>
                    </div>

                    <!-- TABLE DES ARTICLES -->
                    <div class="row mb-3">
                        <div class="col-12">
                            <table class="table table-sm">
                                <thead>
                                    <tr style="background-color: #e9ecef;">
                                        <th>Description</th>
                                        <th class="text-center">Quantité</th>
                                        <th class="text-center">Unité</th>
                                        <th class="text-right">Prix unitaire</th>
                                        <th class="text-right">Montant</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <t t-foreach="doc.invoice_line_ids" t-as="line">
                                        <t t-if="not line.display_type">
                                            <tr>
                                                <td><span t-esc="line.name"/></td>
                                                <td class="text-center">
                                                    <t t-esc="'{:,.0f}'.format(line.quantity)"/>
                                                </td>
                                                <td class="text-center">
                                                    <t t-esc="line.product_uom_id.name or ''"/>
                                                </td>
                                                <td class="text-right">
                                                    <t t-esc="'{:,.2f}'.format(line.price_unit)"/>
                                                </td>
                                                <td class="text-right">
                                                    <t t-esc="'{:,.2f}'.format(line.price_subtotal)"/>
                                                </td>
                                            </tr>
                                        </t>
                                    </t>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- MONTANT TOTAL HT -->
                    <div class="row mb-3">
                        <div class="col-6"/>
                        <div class="col-6">
                            <table class="table table-sm">
                                <tr>
                                    <td colspan="2"><strong>MONTANT TOTAL HT = 
                                        <t t-esc="'{:,.2f}'.format(doc.amount_untaxed) + ' CFA'"/>
                                    </strong></td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <!-- SECTION ACOMPTES -->
                    <div class="row mb-3">
                        <div class="col-12">
                            <h5>ACOMPTES</h5>
                            <table class="table table-sm">
                                <tbody>
                                    <t t-set="previous_dps" t-value="doc._get_previous_downpayments()"/>
                                    <t t-foreach="previous_dps" t-as="dp">
                                        <tr>
                                            <td>Acompte n°<t t-esc="dp['sequence']"/>, 
                                                FACTURE N° <t t-esc="dp['invoice_name']"/> 
                                                du <t t-esc="dp['invoice_date']"/>
                                            </td>
                                            <td class="text-right">
                                                <t t-esc="'{:,.2f}'.format(dp['amount_total']) + ' CFA'"/>
                                            </td>
                                        </tr>
                                    </t>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- TOTAL ACOMPTES ET SOLDE -->
                    <div class="row">
                        <div class="col-6"/>
                        <div class="col-6">
                            <table class="table table-sm">
                                <tr>
                                    <td><strong>TOTAL ACOMPTES PAYÉS</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(doc.total_downpayments_paid) + ' CFA'"/>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>SOLDE HT</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(doc.amount_untaxed - doc.total_downpayments_paid) + ' CFA'"/>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>TVA 18%</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(doc.amount_tax) + ' CFA'"/>
                                    </td>
                                </tr>
                                <tr style="background-color: #f0f0f0; font-weight: bold;">
                                    <td><strong>MONTANT NET A PAYER</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(doc.amount_total) + ' CFA'"/>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <!-- FOOTER -->
                    <div class="row mt-4 pt-2" style="border-top: 2px solid #ccc;">
                        <div class="col-12 text-center">
                            <p style="font-size: 10px; color: #666;">
                                Toute réclamation concernant la conformité des produits / services 
                                doit être formulée par écrit dans un délai de 15 jours suivant la réception de la facture
                            </p>
                        </div>
                    </div>

                </div>
            </t>
        </template>

    </data>
</odoo>
```

#### **7.4 Template : First Down Payment Invoice**

```xml
<!-- reports/templates/first_down_payment_invoice_1.xml -->

<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        <template id="first_down_payment_invoice_1_template">
            <t t-call="web.external_layout">
                <div class="page">
                    
                    <!-- HEADER -->
                    <div class="row mb-4">
                        <div class="col-7">
                            <img t-if="doc.company_id.logo" 
                                 t-att-src="image_data_uri(doc.company_id.logo)" 
                                 style="max-height: 100px;" alt="Logo"/>
                        </div>
                        <div class="col-5 text-right">
                            <h2 class="mt-4">FACTURE</h2>
                            <p class="mt-2"><strong t-field="doc.name"/></p>
                            <p><t t-esc="doc.invoice_date.strftime('%d/%m/%Y') if doc.invoice_date else ''"/></p>
                        </div>
                    </div>

                    <!-- INFOS CLIENT -->
                    <div class="row mb-3">
                        <div class="col-6">
                            <strong>DE :</strong>
                            <p t-field="doc.company_id.name"/>
                        </div>
                        <div class="col-6">
                            <strong>DOIT :</strong>
                            <p t-field="doc.partner_id.name"/>
                        </div>
                    </div>

                    <!-- TABLE DES ARTICLES -->
                    <div class="row mb-3">
                        <div class="col-12">
                            <table class="table table-sm">
                                <thead>
                                    <tr style="background-color: #e9ecef;">
                                        <th>Description</th>
                                        <th class="text-center">Quantité</th>
                                        <th class="text-center">Unité</th>
                                        <th class="text-right">Prix unitaire</th>
                                        <th class="text-right">Montant</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <t t-foreach="doc.invoice_line_ids" t-as="line">
                                        <t t-if="not line.display_type">
                                            <tr>
                                                <td><span t-esc="line.name"/></td>
                                                <td class="text-center">
                                                    <t t-esc="'{:,.0f}'.format(line.quantity)"/>
                                                </td>
                                                <td class="text-center">
                                                    <t t-esc="line.product_uom_id.name or ''"/>
                                                </td>
                                                <td class="text-right">
                                                    <t t-esc="'{:,.2f}'.format(line.price_unit)"/>
                                                </td>
                                                <td class="text-right">
                                                    <t t-esc="'{:,.2f}'.format(line.price_subtotal)"/>
                                                </td>
                                            </tr>
                                        </t>
                                    </t>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- MONTANT TOTAL HT -->
                    <div class="row mb-3">
                        <div class="col-6"/>
                        <div class="col-6">
                            <table class="table table-sm">
                                <tr>
                                    <td colspan="2"><strong>MONTANT TOTAL HT = 
                                        <t t-esc="'{:,.2f}'.format(doc.amount_untaxed) + ' CFA'"/>
                                    </strong></td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <!-- SECTION ACOMPTES -->
                    <div class="row mb-3">
                        <div class="col-12">
                            <h5>ACOMPTES</h5>
                            <table class="table table-sm">
                                <tbody>
                                    <tr>
                                        <td><strong>Acompte n°1 à payer (20%)</strong></td>
                                        <td class="text-right">
                                            <t t-esc="'{:,.2f}'.format(doc.amount_untaxed * 0.20) + ' CFA'"/>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- TOTAUX ACOMPTE -->
                    <t t-set="downpayment_amount" t-value="doc.amount_untaxed * 0.20"/>
                    <div class="row">
                        <div class="col-6"/>
                        <div class="col-6">
                            <table class="table table-sm">
                                <tr>
                                    <td><strong>MONTANT</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(downpayment_amount) + ' CFA'"/>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>TVA 18%</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(downpayment_amount * 0.18) + ' CFA'"/>
                                    </td>
                                </tr>
                                <tr style="background-color: #f0f0f0; font-weight: bold;">
                                    <td><strong>MONTANT NET A PAYER</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(downpayment_amount * 1.18) + ' CFA'"/>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>RESTE A PAYER</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(doc.amount_untaxed * 0.80) + ' CFA'"/>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <!-- FOOTER -->
                    <div class="row mt-4 pt-2" style="border-top: 2px solid #ccc;">
                        <div class="col-12 text-center">
                            <p style="font-size: 10px; color: #666;">
                                Toute réclamation concernant la conformité des produits / services 
                                doit être formulée par écrit dans un délai de 15 jours suivant la réception de la facture
                            </p>
                        </div>
                    </div>

                </div>
            </t>
        </template>

    </data>
</odoo>
```

#### **7.5 Template : Nth Down Payment Invoice**

```xml
<!-- reports/templates/nth_down_payment_invoice.xml -->

<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        <template id="nth_down_payment_invoice_template">
            <t t-call="web.external_layout">
                <div class="page">
                    
                    <!-- HEADER -->
                    <div class="row mb-4">
                        <div class="col-7">
                            <img t-if="doc.company_id.logo" 
                                 t-att-src="image_data_uri(doc.company_id.logo)" 
                                 style="max-height: 100px;" alt="Logo"/>
                        </div>
                        <div class="col-5 text-right">
                            <h2 class="mt-4">FACTURE</h2>
                            <p class="mt-2"><strong t-field="doc.name"/></p>
                            <p><t t-esc="doc.invoice_date.strftime('%d/%m/%Y') if doc.invoice_date else ''"/></p>
                        </div>
                    </div>

                    <!-- INFOS CLIENT -->
                    <div class="row mb-3">
                        <div class="col-6">
                            <strong>DE :</strong>
                            <p t-field="doc.company_id.name"/>
                        </div>
                        <div class="col-6">
                            <strong>DOIT :</strong>
                            <p t-field="doc.partner_id.name"/>
                        </div>
                    </div>

                    <!-- TABLE DES ARTICLES -->
                    <div class="row mb-3">
                        <div class="col-12">
                            <table class="table table-sm">
                                <thead>
                                    <tr style="background-color: #e9ecef;">
                                        <th>Description</th>
                                        <th class="text-center">Quantité</th>
                                        <th class="text-center">Unité</th>
                                        <th class="text-right">Prix unitaire</th>
                                        <th class="text-right">Montant</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <t t-foreach="doc.invoice_line_ids" t-as="line">
                                        <t t-if="not line.display_type">
                                            <tr>
                                                <td><span t-esc="line.name"/></td>
                                                <td class="text-center">
                                                    <t t-esc="'{:,.0f}'.format(line.quantity)"/>
                                                </td>
                                                <td class="text-center">
                                                    <t t-esc="line.product_uom_id.name or ''"/>
                                                </td>
                                                <td class="text-right">
                                                    <t t-esc="'{:,.2f}'.format(line.price_unit)"/>
                                                </td>
                                                <td class="text-right">
                                                    <t t-esc="'{:,.2f}'.format(line.price_subtotal)"/>
                                                </td>
                                            </tr>
                                        </t>
                                    </t>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- MONTANT TOTAL HT -->
                    <div class="row mb-3">
                        <div class="col-6"/>
                        <div class="col-6">
                            <table class="table table-sm">
                                <tr>
                                    <td colspan="2"><strong>MONTANT TOTAL HT = 
                                        <t t-esc="'{:,.2f}'.format(doc.amount_untaxed) + ' CFA'"/>
                                    </strong></td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <!-- SECTION ACOMPTES (acomptes précédents) -->
                    <div class="row mb-3">
                        <div class="col-12">
                            <h5>ACOMPTES</h5>
                            <table class="table table-sm">
                                <tbody>
                                    <t t-set="previous_dps" t-value="doc._get_previous_downpayments()"/>
                                    <t t-foreach="previous_dps" t-as="dp">
                                        <tr>
                                            <td>Acompte n°<t t-esc="dp['sequence']"/>, 
                                                FACTURE N° <t t-esc="dp['invoice_name']"/> 
                                                du <t t-esc="dp['invoice_date']"/>
                                            </td>
                                            <td class="text-right">
                                                <t t-esc="'{:,.2f}'.format(dp['amount_total']) + ' CFA'"/>
                                            </td>
                                        </tr>
                                    </t>
                                </tbody>
                            </table>
                            
                            <table class="table table-sm">
                                <tr>
                                    <td colspan="2"><strong>TOTAL DES ACOMPTES PAYÉS = 
                                        <t t-esc="'{:,.2f}'.format(doc.total_downpayments_paid) + ' CFA'"/>
                                    </strong></td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <!-- NOUVEL ACOMPTE -->
                    <div class="row mb-3">
                        <div class="col-12">
                            <table class="table table-sm">
                                <tbody>
                                    <t t-set="ordinal" t-value="doc._get_ordinal_number(doc.downpayment_sequence_number)"/>
                                    <tr>
                                        <td><strong>Acompte n°<t t-esc="doc.downpayment_sequence_number"/> 
                                            à payer (15%)</strong></td>
                                        <td class="text-right">
                                            <t t-esc="'{:,.2f}'.format(doc.amount_untaxed * 0.15) + ' CFA'"/>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- TOTAUX -->
                    <div class="row">
                        <div class="col-6"/>
                        <div class="col-6">
                            <table class="table table-sm">
                                <tr>
                                    <td><strong>MONTANT HT</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(doc.amount_untaxed) + ' CFA'"/>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>TVA 18%</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(doc.amount_tax) + ' CFA'"/>
                                    </td>
                                </tr>
                                <tr style="background-color: #f0f0f0; font-weight: bold;">
                                    <td><strong>MONTANT NET A PAYER</strong></td>
                                    <td class="text-right">
                                        <t t-esc="'{:,.2f}'.format(doc.amount_total) + ' CFA'"/>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>RESTE A PAYER</strong></td>
                                    <td class="text-right">
                                        <t t-set="remaining" 
                                           t-value="(doc.sale_order_id.amount_untaxed if doc.sale_order_id else doc.amount_untaxed) - doc.total_downpayments_paid - doc.amount_untaxed"/>
                                        <t t-esc="'{:,.2f}'.format(max(0, remaining)) + ' CFA'"/>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <!-- FOOTER -->
                    <div class="row mt-4 pt-2" style="border-top: 2px solid #ccc;">
                        <div class="col-12 text-center">
                            <p style="font-size: 10px; color: #666;">
                                Toute réclamation concernant la conformité des produits / services 
                                doit être formulée par écrit dans un délai de 15 jours suivant la réception de la facture
                            </p>
                        </div>
                    </div>

                </div>
            </t>
        </template>

    </data>
</odoo>
```

---

### **8. FICHIERS DE CONFIGURATION**

#### **8.1 __manifest__.py**

```python
{
    'name': 'Custom Invoice Report Personalization',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Customize invoice reports with dynamic template selection',
    'description': '''
        This module allows personalized invoice report generation based on invoice type:
        
        - Simple Invoices: Full payment in one invoice
        - Final Invoices: Settlement invoice after down payments
        - Down Payment Invoices: Partial payment invoices (1st, 2nd, 3rd, etc.)
        
        The template is automatically selected based on user choice (popup dialog at creation)
        and the number of previous down payments.
        
        Features:
        - Popup dialog to select invoice type at creation
        - Automatic template selection
        - Works with and without Sale Orders
        - Supports unlimited down payments
    ''',
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'license': 'LGPL-3',
    
    'depends': [
        'account',
        'sale',
        'web',
    ],
    
    'data': [
        'security/ir.model.access.csv',
        'views/invoice_type_wizard_views.xml',
        'views/account_move_views.xml',
        'reports/invoice_report.xml',
        'reports/templates/simple_invoice_1.xml',
        'reports/templates/final_invoice.xml',
        'reports/templates/first_down_payment_invoice_1.xml',
        'reports/templates/nth_down_payment_invoice.xml',
    ],
    
    'external_dependencies': {
        'python': [],
    },
    
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 10,
}
```

#### **8.2 __init__.py**

```python
# models/__init__.py

from . import account_move_extension
from . import invoice_type_wizard
```

```python
# views/__init__.py
# Fichier vide - Odoo charge automatiquement les XML
```

```python
# reports/__init__.py
# Fichier vide - Odoo charge automatiquement les rapports
```

#### **8.3 security/ir.model.access.csv**

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_invoice_type_wizard_user,Invoice Type Wizard - User,model_account_move_invoice_type_wizard,base.group_user,1,1,1,0
access_invoice_type_wizard_manager,Invoice Type Wizard - Manager,model_account_move_invoice_type_wizard,account.group_account_manager,1,1,1,1
```

---

## 📋 PROMPT FINAL À UTILISER AVEC LE LLM

```
Tu es un expert Odoo 18. Crée un module COMPLET et PROFESSIONNEL pour personnaliser 
les rapports de facturation avec les spécifications suivantes :

=== CONTEXTE ===
- Module pour Odoo 18+
- Compatible avec et sans Sale Order
- Popup de sélection du type de facture au moment de la création

=== TYPES DE FACTURES ===

1. FACTURE NORMALE
   - Utilisateur sélectionne via popup : "Facture Normale/Simple"
   - Cas A1 : Aucun acompte précédent → Template: "simple_invoice_1"
   - Cas A2 : Acomptes existants → Template: "final_invoice"

2. FACTURE D'ACOMPTE  
   - Utilisateur sélectionne via popup : "Facture d'Acompte"
   - Cas B1 : Premier acompte (count=1) → Template: "first_down_payment_invoice_1"
   - Cas B2 : Acomptes suivants (count≥2) → Template: "2nd/3rd/4th_down_payment_invoice_1"

=== POPUP DE SÉLECTION ===
- S'affiche lors de la création/modification brouillon d'une facture
- Bouton "Sélectionner Type de Facture" dans le formulaire
- Dialog avec deux options radio :
  ☐ Facture Normale/Simple
  ☐ Facture d'Acompte
- Affiche le nombre d'acomptes existants pour cette SO/Devis
- Confirmation → Enregistre le type et recalcule les templates

=== MODÈLES REQUIS ===

account.move (Extension) :
  - invoice_type (Selection: 'normal' / 'downpayment')
  - downpayment_sequence_number (Integer)
  - previous_downpayments_count (Computed)
  - total_downpayments_paid (Computed)
  - custom_report_template (Selection, Computed)
  - Méthodes : _get_previous_downpayments(), _get_ordinal_number()

account.move.invoice.type.wizard (Transient) :
  - Dialog popup pour sélection du type
  - Message informatif avec contexte

=== TEMPLATES QWEB ===
- 5 templates basés sur les PDFs fournis
- Sélection conditionnelle dans template principal
- Variables formatées : CFA, pourcentages, dates

=== DONNÉES FOURNIES ===
[PDFs de référence: simple_invoice_1, final_invoice, 
 first_down_payment_invoice_1, 2nd_down_payment_invoice_1, 3rd_down_payment_invoice_1]

=== GÉNÉRER ===
1. Code Python complet (models, wizard)
2. Views XML (form, tree, wizard popup)
3. Reports XML (templates + rapport principal)
4. Security CSV
5. __manifest__.py
6. Tests unitaires
7. Documentation PDF
```