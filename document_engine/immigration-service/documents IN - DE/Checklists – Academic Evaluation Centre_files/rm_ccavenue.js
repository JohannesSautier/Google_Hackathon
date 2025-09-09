jQuery(document).ready(function(e){
    

    jQuery('#rm-ccavenue-paylater').click(function(){
       jQuery('#rm-ccavenue-paylater-form').submit();
    });

    jQuery('.rm_payment_method_select').change(function(e){
       let pmethod = jQuery(this).val();
       if(pmethod === 'ccavenue'){
           jQuery(this).closest('fieldset').find('.rmagic-row:not(.rm_payment_options)').hide(400);
           jQuery(this).closest('fieldset').find('.cc-avenue-hidden').hide(400);
           jQuery(this).closest('fieldset').find('.rmagic-row:not(.rm_payment_options) .rmagic-field:not(.rm_pricefield_row) input:not(.rm_price_field_quantity)').val('');
       }else{
           jQuery(this).closest('fieldset').find('.rmagic-row:not(.rm_payment_options)').show(400);
           jQuery(this).closest('fieldset').find('.cc-avenue-hidden').show(400);
       }
   });

});